from chia.base.ChiaFunction import ChiaFunction, get
import ray


@ChiaFunction()
def hello(name):
    return f"Hello from CHIA, {name}!"


if __name__ == "__main__":
    ray.init()

    ref = hello.chia_remote("CHIA")
    print(get(ref))

    ray.shutdown()