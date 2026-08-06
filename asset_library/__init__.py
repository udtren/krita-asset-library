"""Krita plugin entry point for Asset Library."""

from krita import Extension, Krita

from .docker import AssetLibraryDockerFactory


class AssetLibraryExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.asset_library_docker_factory = None

    def setup(self):
        self.asset_library_docker_factory = AssetLibraryDockerFactory()
        Krita.instance().addDockWidgetFactory(self.asset_library_docker_factory)

    def createActions(self, window):
        pass


app = Krita.instance()
app.addExtension(AssetLibraryExtension(app))