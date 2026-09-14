"""Very short CPU-only YuE2 generation smoke test."""
import json
import os
from pathlib import Path

import torch
from yue2 import YuE2Pipeline


def main():
    if torch.cuda.is_available():
        raise RuntimeError("The CPU smoke test unexpectedly sees CUDA")
    torch.set_num_threads(int(os.environ.get("YUE2_CPU_THREADS", "4")))

    output = Path("/outputs/cpu-smoke.wav")
    output.parent.mkdir(parents=True, exist_ok=True)
    with YuE2Pipeline.from_pretrained(
        "/weights/model",
        vae="/weights/vae",
        local_files_only=True,
        device="cpu",
        backend="torch-eager",
        memory_budget_gib=8,
        progress=True,
    ) as pipe:
        # cot=off skips symbolic planning. Thirty-two codec tokens make a
        # deliberately tiny, truncated sample while exercising AR, NAR, VAE,
        # CPU attention, and audio serialization.
        song = pipe(
            id="cpu-smoke",
            style="minimal electronic tone, no vocal, very short test signal",
            lyrics="[Verse]\nHello CPU\n[End]",
            cot="off",
            seed=7,
            semantic_sampling={
                "temperature": 0.0,
                "top_k": 1,
                "min_tokens": 32,
                "max_tokens": 32,
            },
        )
        song.save(output)

    audio = song.audio
    result = {
        "device": "cpu",
        "backend": "torch-eager",
        "sample_rate": song.sample_rate,
        "shape": list(audio.shape),
        "seconds": len(audio) / song.sample_rate,
        "finite": bool(torch.isfinite(torch.from_numpy(audio)).all()),
        "truncated": song.truncated,
        "output": str(output),
    }
    print(json.dumps(result, indent=2))
    if not result["finite"] or result["shape"][1] != 2:
        raise RuntimeError(f"Invalid CPU smoke audio: {result}")


if __name__ == "__main__":
    main()
