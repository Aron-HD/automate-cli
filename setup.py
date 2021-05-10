from setuptools import setup, find_packages


def read_requirements():
    # remember to pip freeze cat > requirements.txt
    with open('requirements.txt') as req:
        content = req.read().split('\n')

    return content


setup(
        name='automate',
        version='0.1',
        packages=find_packages(),
        include_package_data=True,
        install_requires=read_requirements(),
        entry_points='''
		[console_scripts]
		automate=automate.cli:cli
	'''
)
