Overview
========

Generates project files for numerous compilers, IDE:s and makefiles from a XML definition file.

XML tags
--------
* *target*. Either an executable or library.
* *dependency*. Includes another XML-definition to the target. Either merges it in or depends on the library it produces.
* *source*. Includes all found (source) files in the specified directory. Optionally can include all sub directories recursively.
* *header*. Search path for include files.
* *define*. Adds a preprocessor define.
* *library-path*. Paths to library files.
* *configuration*. Defines a configuration. Defaults are "debug", "release", "internal" and "distribution".
* *platform*. Platform-specific options are placed inside this tag scope.


Sample XML file
---------------

```xml
<target name="my-project" type="executable">
	<dependency filename="some_other.xml" merge="true" />

	<header directory="include/render" />
	<header directory="../external/libogg-1.3.0/include" />

	<source directory="source/sound" recursive="true" />
	<source directory="source/thread" />

	<library-path directory="lib/" />

	<configuration name="debug">
		<define name="HAVE_ALLOC_H" />
	</configuration>

	<platform name="mac_os_x">
		<library filename="Cocoa.framework" />
		<library filename="OpenGL.framework" />
	</platform>

	<platform name="linux">
		<source directory="source/posix" exclude="[main.c]"/>
		<library filename="GL" />
		<library filename="pulse-simple" />

		<configuration name="debug">
			<define name="LINUX_DEBUG" value="1" />
		</configuration>

	</platform>
</target>
```

Command line
------------

    generate.py -i <xml file> -p <platform> -g <generator> -n <override with target name> -d <optional path to data> -r <optional path to resource files>

### Generators

* visualc
* xcode
* makefile
* codelite
* codeblocks

### Platform.

Can be any string, but recommended are:

* mac_os_x
* windows
* linux
