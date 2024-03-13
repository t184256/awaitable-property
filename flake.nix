{
  description = "@awaitable_property decorator, lets you await obj.attrname";

  outputs = { self, nixpkgs, flake-utils }:
    let
      pyDeps = pyPackages: with pyPackages; [
        # TODO: list python dependencies
      ];
      pyTestDeps = pyPackages: with pyPackages; [
        pytest pytestCheckHook pytest-asyncio
        coverage pytest-cov
      ];
      pyTools = pyPackages: with pyPackages; [ mypy ];

      tools = pkgs: with pkgs; [
        pre-commit
        ruff
        codespell
        actionlint
        python3Packages.pre-commit-hooks
      ];

      awaitable-property-package = {pkgs, python3Packages}:
        python3Packages.buildPythonPackage {
          pname = "awaitable-property";
          version = "0.0.1";
          src = ./.;
          disabled = python3Packages.pythonOlder "3.11";
          format = "pyproject";
          build-system = [ python3Packages.setuptools ];
          propagatedBuildInputs = pyDeps python3Packages;
          checkInputs = pyTestDeps python3Packages;
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
            buildInputs = [(defaultPython3Packages.python.withPackages (
              pyPkgs: pyDeps pyPkgs ++ pyTestDeps pyPkgs ++ pyTools pyPkgs
            ))];
            nativeBuildInputs = [(pkgs.buildEnv {
              name = "awaitable-property-tools-env";
              pathsToLink = [ "/bin" ];
              paths = tools pkgs;
            })];
            shellHook = ''
              [ -e .git/hooks/pre-commit ] || \
                echo "suggestion: pre-commit install --install-hooks" >&2
              export PYTHONASYNCIODEBUG=1 PYTHONWARNINGS=error
            '';
          };
          packages.awaitable-property = awaitable-property;
          packages.default = awaitable-property;
        }
    ) // { overlays.default = awaitable-property-overlay; };
}
