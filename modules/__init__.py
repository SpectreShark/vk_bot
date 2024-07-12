from typing import Type, Any

DEPENDENCIES_TYPE = dict[Type["Module"], Any]


class Module:
    dependencies: DEPENDENCIES_TYPE = {}
    required_dependencies: list[Type["Module"]] = []

    async def on_load(self, *args, **kwargs) -> None:
        pass

    async def on_unload(self) -> None:
        pass


class ModuleManager:
    def __init__(self) -> None:
        self.modules: dict[Type[Module], dict[str, Any]] = {}
        self.__loaded_modules: dict[Type[Module], Module] = {}

    def add_module(self, module: Type[Module], args: dict[str, Any] = {}) -> None:
        self.modules[module] = args

    def remove_module(self, module: Type[Module]) -> None:
        self.modules.pop(module)

    def is_loaded(self, module: Type[Module]) -> bool:
        return module in self.__loaded_modules

    async def __load_module(self, module: Type[Module]) -> None:
        if not self.modules.__contains__(module):
            raise Exception(f"Module {module} not registered")

        for dependency in module.required_dependencies:
            if not self.is_loaded(dependency):
                await self.__load_module(dependency)
            module.dependencies[dependency] = self.__loaded_modules[dependency]

        instance = module()
        await instance.on_load(**self.modules[module])
        self.__loaded_modules[module] = instance

    async def load_modules(self) -> None:
        for module in self.modules.keys():
            await self.__load_module(module)

    async def unload_modules(self) -> None:
        for module in self.modules.keys():
            await self.__loaded_modules[module].on_unload()
