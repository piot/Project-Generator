Overview
========

Generates project files for numerous compilers, IDE:s and makefiles from a XML definition file.

Sample XML file
---------------

	<target name="my-project" type="executable">
		<header directory="include/render" />
		<source directory="lib/sounds" />
		<header directory="../external/libogg-1.3.0/include" />

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

Command line
------------

	generate.py -i <xml file> -p <platform> -g <generator> -n <override with name> -d <optional path to data> -r <optional path to resource files>
