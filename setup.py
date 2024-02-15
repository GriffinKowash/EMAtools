from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
#long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="EMAtools",  # Required
    version="0.0.4",  # Required
    description="An assortment of computational tools to make life easier at EMA.",  # Optional
    #long_description=long_description,  # Optional
    #long_description_content_type="text/markdown",  # Optional (see note above)
    url="https://github.com/GriffinKowash/EMAtools",  # Optional
    author="Griffin Kowash",  # Optional
    author_email="griffin.kowash@ema3d.com",  # Optional
    package_dir={"": "src"},  # Optional
    packages=find_packages(where="src"),  # Required
    python_requires=">=3.7, <4",
    install_requires=["numpy", "scipy"]  # Optional
)