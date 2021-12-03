import setuptools

name = "masmbl"

version = "0.1"

description = "Customisable assembler for mips and mips variants."

python_requires = ">=3.8"

packages = ["masmbl"]

install_requires = ["pyyaml", "bitstring"]

setuptools.setup(
    name=name,
    version=version,
    description=description,
    python_requires=python_requires,
    packages=packages,
    install_requires=install_requires,
    package_data={'masmbl': ['*.yaml', 'masmbl/*.yaml']},
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["masmbl = masmbl.mips_asmbl:main"]},
)
