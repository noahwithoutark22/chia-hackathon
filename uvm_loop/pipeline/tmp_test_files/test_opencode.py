import ray

from chia.base.ChiaFunction import get
from chia.models.opencode import OpenCodeLLM


if __name__ == "__main__":
    ray.init()

    llm = OpenCodeLLM(
        model="opencode/big-pickle",
        work_dir="/workspace",
    )

    ref = llm.prompt.chia_remote(
        llm,
        "Reply with exactly: CHIA_OPENCODE_OK",
    )

    result = get(ref)

    print("CHIA returned:")
    print(result)

    ray.shutdown()