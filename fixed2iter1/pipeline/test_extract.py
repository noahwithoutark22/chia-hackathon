import ray

from chia.base.ChiaFunction import get

from pipeline.functions import extract_rtl


if __name__ == "__main__":
    ray.init()

    ref = extract_rtl.chia_remote(
        "examples/adder/adder.sv",
        "generated/rtl/rtl_info.json",
    )

    result = get(ref)

    print("CHIA returned:")
    print(result)

    ray.shutdown()