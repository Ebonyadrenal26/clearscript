"""FastAPI server for the local web UI.

Single-page app served at ``/``; JSON API under ``/api/*``. The whole thing
binds to 127.0.0.1 by default — never exposes itself to the network unless
the user explicitly passes ``--host 0.0.0.0``.
"""

from __future__ import annotations

import contextlib
import tempfile
import threading
import time
import webbrowser
from importlib import resources
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from clearscript import __version__
from clearscript.config import Config, ensure_dirs, load_config
from clearscript.core.pipeline import Pipeline
from clearscript.export import write_docx
from clearscript.ingest.txt import TxtAdapter
from clearscript.library import Library
from clearscript.providers import build_provider

# ============ Request/response models (module-level so FastAPI can introspect) ============


class RunRequest(BaseModel):
    transcript: str
    provider: str | None = None
    model: str | None = None
    title: str | None = None
    briefing: str | None = None


class RunResponse(BaseModel):
    edited_markdown: str
    change_log: list[dict]
    suggestions: list[dict]
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class ExportRequest(BaseModel):
    markdown: str
    title: str | None = None


class TermPayload(BaseModel):
    canonical: str = ""
    type: str | None = Field(default=None)
    domain: str | None = None
    status: str | None = None
    definition: str | None = None
    notes: str | None = None
    aliases: list[str] = []


class SpeakerPayload(BaseModel):
    canonical_name: str = ""
    display_label: str = ""
    primary_language: str | None = None
    notes: str | None = None
    aliases: list[str] = []


class PatternPayload(BaseModel):
    title: str
    trigger_desc: str
    action: str
    rationale: str | None = None
    domain: str | None = None


class SuggestionItem(BaseModel):
    kind: str
    canonical: str | None = None
    canonical_name: str | None = None
    display_label: str | None = None
    type: str | None = None
    domain: str | None = None
    aliases_seen: list[str] = []
    title: str | None = None
    trigger_desc: str | None = None
    action: str | None = None
    rationale: str | None = None


class AcceptSuggestionsRequest(BaseModel):
    suggestions: list[SuggestionItem]


# ============ App factory ============


def create_app() -> FastAPI:
    app = FastAPI(title="clearscript", version=__version__)
    cfg_holder: dict[str, Config] = {}

    def cfg() -> Config:
        if "config" not in cfg_holder:
            c = load_config()
            ensure_dirs(c)
            cfg_holder["config"] = c
        return cfg_holder["config"]

    def open_library() -> Library:
        return Library(cfg().library_path)

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        html = (
            resources.files("clearscript.web").joinpath("index.html").read_text(encoding="utf-8")
        )
        return HTMLResponse(html)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/api/providers")
    def list_providers() -> dict:
        c = cfg()
        return {
            "default": c.default_provider,
            "providers": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default_model": p.default_model,
                    "models": p.models,
                    "has_key": (p.resolve_api_key() is not None) or p.type == "ollama",
                    "key_env": p.api_key_env,
                }
                for p in c.providers.values()
            ],
        }

    @app.post("/api/run", response_model=RunResponse)
    def run_pipeline(req: RunRequest) -> RunResponse:
        if not req.transcript.strip():
            raise HTTPException(400, "Transcript is empty.")

        c = cfg()
        try:
            provider_cfg = c.get_provider(req.provider)
        except KeyError as exc:
            raise HTTPException(400, str(exc)) from exc

        chosen_model = req.model or provider_cfg.default_model
        if not chosen_model:
            raise HTTPException(
                400,
                f"No model specified and provider {provider_cfg.name!r} has no default. "
                "Pick one in the model dropdown.",
            )

        try:
            llm = build_provider(provider_cfg)
        except RuntimeError as exc:
            raise HTTPException(400, str(exc)) from exc

        adapter = TxtAdapter()
        transcript = adapter.parse_string(req.transcript)

        library = open_library()
        try:
            pipeline = Pipeline(
                provider=llm,
                model=chosen_model,
                library=library,
                briefing_context=req.briefing or "",
            )
            try:
                result = pipeline.run_on_transcript(transcript)
            except Exception as exc:
                raise HTTPException(500, f"Pipeline error: {exc}") from exc
        finally:
            library.close()

        return RunResponse(
            edited_markdown=result.edited_markdown,
            change_log=result.change_log,
            suggestions=result.suggestions,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            model=result.model,
            provider=result.provider,
        )

    @app.post("/api/export/docx")
    def export_docx(req: ExportRequest) -> Response:
        if not req.markdown.strip():
            raise HTTPException(400, "Nothing to export.")

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            out_path = Path(tmp.name)
        try:
            write_docx(req.markdown, out_path, title=req.title)
            data = out_path.read_bytes()
        finally:
            with contextlib.suppress(FileNotFoundError):
                out_path.unlink()

        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="clearscript-output.docx"'},
        )

    @app.get("/api/example")
    def get_example() -> dict:
        examples_root = (
            Path(__file__).resolve().parent.parent.parent / "examples" / "01-basic-cleanup"
        )
        input_path = examples_root / "input.txt"
        if input_path.is_file():
            return {"transcript": input_path.read_text(encoding="utf-8")}
        return {"transcript": ""}

    # ============ Library: stats ============

    @app.get("/api/library/stats")
    def library_stats() -> dict:
        lib = open_library()
        try:
            return lib.stats()
        finally:
            lib.close()

    # ============ Library: terms ============

    @app.get("/api/library/terms")
    def list_terms_endpoint(
        type: str | None = None,
        domain: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int = 500,
    ) -> dict:
        lib = open_library()
        try:
            return {
                "terms": lib.list_terms(
                    type_=type, domain=domain, status=status, search=search, limit=limit
                )
            }
        finally:
            lib.close()

    @app.post("/api/library/terms", status_code=201)
    def add_term_endpoint(payload: TermPayload) -> dict:
        if not payload.canonical.strip():
            raise HTTPException(400, "canonical is required")
        lib = open_library()
        try:
            term_id = lib.add_term(
                canonical=payload.canonical,
                type_=payload.type,
                domain=payload.domain,
                aliases=payload.aliases,
                definition=payload.definition,
            )
            if payload.status:
                lib.update_term(term_id, status=payload.status)
            return {"id": term_id}
        finally:
            lib.close()

    @app.patch("/api/library/terms/{term_id}")
    def update_term_endpoint(term_id: int, payload: TermPayload) -> dict:
        lib = open_library()
        try:
            lib.update_term(
                term_id,
                canonical=payload.canonical or None,
                type_=payload.type,
                domain=payload.domain,
                status=payload.status,
                definition=payload.definition,
                notes=payload.notes,
                aliases=payload.aliases if payload.aliases else None,
            )
            return {"ok": True}
        finally:
            lib.close()

    @app.delete("/api/library/terms/{term_id}", status_code=204)
    def delete_term_endpoint(term_id: int) -> Response:
        lib = open_library()
        try:
            lib.delete_term(term_id)
            return Response(status_code=204)
        finally:
            lib.close()

    # ============ Library: speakers ============

    @app.get("/api/library/speakers")
    def list_speakers_endpoint(search: str | None = None, limit: int = 500) -> dict:
        lib = open_library()
        try:
            return {"speakers": lib.list_speakers(search=search, limit=limit)}
        finally:
            lib.close()

    @app.post("/api/library/speakers", status_code=201)
    def add_speaker_endpoint(payload: SpeakerPayload) -> dict:
        if not payload.canonical_name.strip() or not payload.display_label.strip():
            raise HTTPException(400, "canonical_name and display_label are required")
        lib = open_library()
        try:
            sid = lib.add_speaker(
                canonical_name=payload.canonical_name,
                display_label=payload.display_label,
                aliases=payload.aliases,
                primary_language=payload.primary_language,
            )
            return {"id": sid}
        finally:
            lib.close()

    @app.patch("/api/library/speakers/{speaker_id}")
    def update_speaker_endpoint(speaker_id: int, payload: SpeakerPayload) -> dict:
        lib = open_library()
        try:
            lib.update_speaker(
                speaker_id,
                canonical_name=payload.canonical_name or None,
                display_label=payload.display_label or None,
                primary_language=payload.primary_language,
                notes=payload.notes,
                aliases=payload.aliases if payload.aliases else None,
            )
            return {"ok": True}
        finally:
            lib.close()

    @app.delete("/api/library/speakers/{speaker_id}", status_code=204)
    def delete_speaker_endpoint(speaker_id: int) -> Response:
        lib = open_library()
        try:
            lib.delete_speaker(speaker_id)
            return Response(status_code=204)
        finally:
            lib.close()

    # ============ Library: edit patterns ============

    @app.get("/api/library/patterns")
    def list_patterns_endpoint(domain: str | None = None) -> dict:
        lib = open_library()
        try:
            return {"patterns": lib.list_edit_patterns(domain=domain)}
        finally:
            lib.close()

    @app.post("/api/library/patterns", status_code=201)
    def add_pattern_endpoint(payload: PatternPayload) -> dict:
        lib = open_library()
        try:
            pid = lib.add_edit_pattern(
                title=payload.title,
                trigger_desc=payload.trigger_desc,
                action=payload.action,
                rationale=payload.rationale,
                domain=payload.domain,
            )
            return {"id": pid}
        finally:
            lib.close()

    @app.delete("/api/library/patterns/{pattern_id}", status_code=204)
    def delete_pattern_endpoint(pattern_id: int) -> Response:
        lib = open_library()
        try:
            lib.delete_edit_pattern(pattern_id)
            return Response(status_code=204)
        finally:
            lib.close()

    # ============ Library: bulk accept Mode B suggestions ============

    @app.post("/api/library/accept-suggestions")
    def accept_suggestions(req: AcceptSuggestionsRequest) -> dict:
        lib = open_library()
        accepted = {"terms": 0, "speakers": 0, "patterns": 0, "skipped": 0}
        try:
            for s in req.suggestions:
                kind = s.kind.lower()
                if kind == "term" and s.canonical:
                    lib.add_term(
                        canonical=s.canonical,
                        type_=s.type,
                        domain=s.domain,
                        aliases=s.aliases_seen or [],
                    )
                    accepted["terms"] += 1
                elif kind == "speaker" and s.canonical_name and s.display_label:
                    lib.add_speaker(
                        canonical_name=s.canonical_name,
                        display_label=s.display_label,
                        aliases=s.aliases_seen or [],
                    )
                    accepted["speakers"] += 1
                elif kind == "edit_pattern" and s.title and s.trigger_desc and s.action:
                    lib.add_edit_pattern(
                        title=s.title,
                        trigger_desc=s.trigger_desc,
                        action=s.action,
                        rationale=s.rationale,
                        domain=s.domain,
                    )
                    accepted["patterns"] += 1
                else:
                    accepted["skipped"] += 1
            return {"accepted": accepted}
        finally:
            lib.close()

    return app


def serve(host: str = "127.0.0.1", port: int = 7681, open_browser: bool = True) -> None:
    """Run the local web server (blocking)."""
    import uvicorn

    app = create_app()

    if open_browser:

        def _open() -> None:
            time.sleep(0.8)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")
