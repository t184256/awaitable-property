{
  description = "@awaitable_property decorator, lets you await obj.attrname";

  outputs = { self, nixpkgs, flake-utils }:
    let
      deps = pyPackages: with pyPackages; [
        # TODO: list python dependencies
      ];
      tools = pkgs: pyPackages: (with pyPackages; [
        pytest pytestCheckHook pytest-asyncio
        coverage pytest-cov
        mypy pytest-mypy
      ] ++ [pkgs.ruff]);

      fresh-mypy-overlay = final: prev: {
        pythonPackagesExtensions =
          prev.pythonPackagesExtensions ++ [(pyFinal: pyPrev: {
            mypy =
              if prev.lib.versionAtLeast pyPrev.mypy.version "1.7.0"
              then pyPrev.mypy
              else pyPrev.mypy.overridePythonAttrs (_: {
                version = "1.8.0";
                patches = [];
                src = prev.fetchFromGitHub {
                  owner = "python";
                  repo = "mypy";
                  rev = "refs/tags/v1.8.0";
                  hash = "sha256-1YgAswqLadOVV5ZSi5ZXWYK3p114882IlSx0nKChGPs=";
                };
              });
          })];
      };

      awaitable-property-package = {pkgs, python3Packages}:
        python3Packages.buildPythonPackage {
          pname = "awaitable-property";
          version = "0.0.1";
          src = ./.;
          format = "pyproject";
          propagatedBuildInputs = deps python3Packages;
          nativeBuildInputs = [ python3Packages.setuptools ];
          checkInputs = tools pkgs python3Packages;
        };

      awaitable-property-overlay = final: prev: {
        pythonPackagesExtensions =
          prev.pythonPackagesExtensions ++ [(pyFinal: pyPrev: {
            awaitable-property = final.callPackage awaitable-property-package {
              python3Packages = pyFinal;
            };
          })];
      };

      overlay-all = nixpkgs.lib.composeManyExtensions [
        awaitable-property-overlay
        fresh-mypy-overlay
      ];
    in
      flake-utils.lib.eachDefaultSystem (system:
        let
          pkgs = import nixpkgs { inherit system; overlays = [ overlay-all ]; };
          defaultPython3Packages = pkgs.python311Packages;  # force 3.11

          awaitable-property = pkgs.callPackage awaitable-property-package {
            python3Packages = defaultPython3Packages;
          };
        in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = [(defaultPython3Packages.python.withPackages deps)];
            nativeBuildInputs = tools pkgs defaultPython3Packages;
            shellHook = ''
              export PYTHONASYNCIODEBUG=1 PYTHONWARNINGS=error
            '';
          };
          packages.awaitable-property = awaitable-property;
          packages.default = awaitable-property;
        }
    ) // { overlays.default = awaitable-property-overlay; };
}
