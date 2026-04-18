
from __future__ import annotations

import asyncio
import base64
import json
import os
import tempfile
from typing import Any

from openai import AsyncAzureOpenAI
from aether_sdk import AetherClient, FactoryState


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it in GitHub Actions secrets or your local environment."
        )
    return value


def _get_client() -> AsyncAzureOpenAI:
    """
    Azure OpenAI client using DEPLOYMENT-SCOPED base URL.
    This removes all dependency on AZURE_OPENAI_ENDPOINT.
    """
    return AsyncAzureOpenAI(
        api_key=_required_env("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        base_url=_required_env("AZURE_OPENAI_BASE_URL"),
    )


client = _get_client()


async def analyse_factory_state(state: FactoryState) -> FactoryState:
    """LangGraph-style node: fuse image, audio, and OPC-UA signals and decide action."""

    if not state.get("audio_bytes"):
        raise ValueError("state['audio_bytes'] is required")
    if not state.get("image_bytes"):
        raise ValueError("state['image_bytes'] is required")
    if not isinstance(state.get("opcua_readings"), dict):
        raise ValueError("state['opcua_readings'] must be a dict")

    # 1) Transcribe factory audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(state["audio_bytes"])
        audio_file_path = tmp.name

    try:
        with open(audio_file_path, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model=os.environ.get("AZURE_WHISPER_DEPLOYMENT", "whisper-1"),
                file=f,
                response_format="verbose_json",
            )

        transcript_text = getattr(transcript, "text", "") or ""

        # 2) Fuse CCTV image + transcript + OPC-UA readings
        b64 = base64.b64encode(state["image_bytes"]).decode("utf-8")
        opcua = state["opcua_readings"]

        response = await client.chat.completions.create(
            model=_required_env("AZURE_OPENAI_DEPLOYMENT"),
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an industrial AI safety system. "
                        "Return strict JSON with keys: "
                        "action, severity, anomalies, recommended_action, reasoning. "
                        "Severity is an integer from 1 to 5. "
                        "anomalies must be an array of strings."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                f"OPC-UA live readings:\n{json.dumps(opcua, ensure_ascii=False)}\n\n"
                                f"Audio transcript (last 30s):\n{transcript_text}\n\n"
                                "Identify anomalies, safety hazards, and quality defects. "
                                "Severity 1=nominal, 5=emergency-shutdown."
                            ),
                        },
                    ],
                },
            ],
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

        # Normalize output defensively
        result["anomalies"] = (
            result["anomalies"]
            if isinstance(result.get("anomalies"), list)
            else [str(result.get("anomalies", "unknown anomaly"))]
        )

        try:
            result["severity"] = int(result.get("severity", 1))
        except Exception:
            result["severity"] = 1

        result.setdefault("action", "MONITOR")
        result.setdefault("reasoning", "")

        # 3) Autonomous action
        if result["severity"] >= 4 or result["action"].upper() == "STOP":
            aether = AetherClient(api_key=os.environ.get("AETHER_API_KEY", ""))

            pm_order = await aether.connectors.sap.create_maintenance_order(
                equipment_id=opcua.get("equipment_id"),
                plant=opcua.get("plant_code", "1000"),
                order_type="PM01",
                priority="1",
                short_text=f"AETHER Vision: {result['anomalies'][0]}",
                long_text=result["reasoning"],
                work_centre=opcua.get("work_centre", "MAINT"),
            )

            return {**state, "action": "STOP", "sap_order": pm_order, "analysis": result}

        return {**state, "action": result["action"], "analysis": result}

    finally:
        try:
            os.remove(audio_file_path)
        except OSError:
            pass


# Optional local demo runner
async def _demo():
    sample_state: FactoryState = {
        "image_bytes": b"fake-jpeg-bytes",
        "audio_bytes": b"fake-wav-bytes",
        "opcua_readings": {
            "equipment_id": "MIXER-17",
            "plant_code": "1000",
            "work_centre": "MAINT",
            "temperature_c": 91.4,
            "vibration_mm_s": 7.8,
            "pressure_bar": 5.1,
        },
    }

    result = await analyse_factory_state(sample_state)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(_demo())
