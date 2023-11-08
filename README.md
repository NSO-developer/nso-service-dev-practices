# Good software development practices

Learn more about software development practices you should follow when developing NSO services.

## Objectives

After completing this Lab you will:

- Be able to use Pylint for static analysis of your code
- Learn how to refactor your code for better reusability, maintainability and performance
- Be able to test your code better

# Lint your code

Pylint is a widely used static code analysis tool for Python programming. It assists developers in improving the quality and maintainability of their Python code by analyzing it for potential errors, style inconsistencies, and adherence to coding standards. Pylint evaluates code against a set of predefined rules and conventions, identifying issues such as syntax errors, variable naming inconsistencies, unused variables, and more. It generates detailed reports and provides suggestions for code improvements, helping developers write cleaner, more readable, and efficient Python code. Pylint contributes to better code quality, reduced bugs, and enhanced code maintainability across projects.

When writing Python code for service mapping or other NSO development Pylint is a great tool to use. In the following example you will use it to lint your package code as part of package build process.

Usually packages are built as part of a CI job. By adding the pylint to the `all` target of a package you will make sure the Python code is always linted. With that you prevent that syntactic errors or code ends up in a merge request since for a successful pipeline run you have to fix them.
## Use Pylint for NSO Python package analysis

You will learn how to use Pylint on an existing NSO package that uses Python to implement mapping logic. In the `~/src/` folder you will find the sample loopback package you will work with in this lab.

### Modify package Makefile to include pylint

First add a recipe for running Pylint to the package Makefile. Open Makefile under `~/src/loopback/src/Makefile` and add the the call for `pylint` target to the `all:` target on the first line:  

```Makefile
all: fxs pylint
```

Now add the `pylint` target to the bottom of the `Makefile`, it should look like the following snippet:

```Makefile
pylint:
	pylint --rcfile=.pylintrc ../python/loopback
```

In the pylint target you have specified the .pylintrc file that should be used for linting this package. Generate the rcfile using pylint:

```bash
pylint --generate-rcfile > ~/src/loopback/src/.pylintrc
```

Build the package using `all` target, this will also trigger the `pylint` target you added as a dependency:
```
make -C ~/src/loopback/src/ all
```
Output:
```
developer:~ > make -C ~/src/loopback/src/ all
make: Entering directory '/home/developer/src/loopback/src'
pylint --rcfile=.pylintrc ../python/loopback
************* Module loopback.loopback
/home/developer/src/loopback/python/loopback/loopback.py:1:0: C0114: Missing module docstring (missing-module-docstring)
/home/developer/src/loopback/python/loopback/loopback.py:6:0: C0115: Missing class docstring (missing-class-docstring)
/home/developer/src/loopback/python/loopback/loopback.py:8:4: C0116: Missing function or method docstring (missing-function-docstring)
/home/developer/src/loopback/python/loopback/loopback.py:20:8: W0622: Redefining built-in 'vars' (redefined-builtin)
/home/developer/src/loopback/python/loopback/loopback.py:9:49: W0212: Access to a protected member _path of a client class (protected-access)
/home/developer/src/loopback/python/loopback/loopback.py:29:0: C0115: Missing class docstring (missing-class-docstring)
/home/developer/src/loopback/python/loopback/loopback.py:3:0: C0411: standard import "import ipaddress" should be placed before "import ncs" (wrong-import-order)

------------------------------------------------------------------
Your code has been rated at 6.96/10 (previous run: 6.96/10, +0.00)

make: *** [Makefile:32: pylint] Error 20
make: Leaving directory '/home/developer/src/loopback/src'
```

As you can see pylint detected multiple problems with the loopback package Python code. You will fix some of these problems and change the rcfile to ignore the rest of them.

### Fix problems in Python code

In the printout above you can see that pylint emits different types of messages:

* E: Error - These messages indicate critical issues that are likely to cause problems or errors in your code.
* W: Warning - These messages point out potential issues or code smells that might lead to problems but are not as critical as errors.
* C: Convention - These messages relate to style and coding convention recommendations. They help ensure that your code adheres to a consistent style, making it more readable and maintainable.

You can see that there are no errors detected in the loopback package, so lets first try to fix the warnings. 

The first warning message is:
```
W0622: Redefining built-in 'vars' (redefined-builtin)
/home/developer/src/loopback/python/loopback/loopback.py:8:4: C0116:
```

It says that we are using a variable name that is part of Python built-in keywords. You should avoid that to prevent confusion. Pylint also reports filename and the line number where the problem was detected.

Open the file with the problem and rename the problematic variable from `vars` to `tvars`. Your code should look like this:

```python
        bgp_address = list(net.hosts())[0]
        tvars = ncs.template.Variables()
        tvars.add('MANAGEMENT_ADDRESS', management_address)
        tvars.add('BGP_ADDRESS', bgp_address)
        template.apply('loopback-template', tvars)
```

Re-run the build of the package. The warning should go away and the score should be higher now.

The next error is about the access to the protected member of a client class - class attributes that starts with the underscore should not be accessed by the user code.
```
/home/developer/src/loopback/python/loopback/loopback.py:9:49: W0212: Access to a protected member _path of a client class (protected-access)
```

Let's say you want to make an exception here and keep the access to the `_path` attribute anyway. In this case you can instruct the linter to ignore this line for a specific problem by using the following comment syntax at the end of the problematic line:

```python
        self.log.info('Service create(service=', service._path, ')') # pylint: disable=protected-access
```

Re-run the linter and you will see that now only the convention problems remains. Fix the import ordering problem by placing the import of the ipaddress package before the `import ncs`. The convention is to import Python standard libraries before third party imports.

```python
# -*- mode: python; python-indent: 4 -*-
import ipaddress
import ncs
from ncs.application import Service
```
There are now only documentation related convention messages. In case you want to ignore them package wide you can suppress them by changing the `.pylintrc` file. Open it and find keyword `disable` under MESSAGES CONTROL section. Add the convention messages that are still triggered:
```
disable=raw-checker-failed,
        bad-inline-option,
        locally-disabled,
        file-ignored,
        suppressed-message,
        useless-suppression,
        deprecated-pragma,
        use-symbolic-message-instead,
        C0114,
        C0115,
        C0116
```

Re-run the `make all` command. Now all errors are fixed or suppressed and the build is successful.

```bash
make -C ~/src/loopback/src/ all
```
Output:
```bash
developer:~ > make -C ~/src/loopback/src/ all
pylint --rcfile=.pylintrc ../python/loopback

-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 7.78/10, +2.22)
```

# Write better Python code

In the following section you will refactor Python NSO service callback function. It is intentionally written in a way that does not follow good practices of modularity, reusability and maintainability. With refactoring you will improve the code so that these good practices can be met. 

## Loopback Python example

Open the `~/src/loopback/python/loopback/loopback.py` example again and study its contents. 

```python
# -*- mode: python; python-indent: 4 -*-
import ipaddress
import ncs
from ncs.application import Service


class ServiceCallbacks(Service):
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')') # pylint: disable=protected-access

        management_prefix = service.management_prefix
        self.log.debug(f'Value of management-prefix leaf is {management_prefix}')
        net = ipaddress.IPv4Network(management_prefix)
        management_address = list(net.hosts())[0]

        bgp_prefix = service.bgp_prefix
        self.log.debug(f'Value of bgp-prefix leaf is {bgp_prefix}')
        net = ipaddress.IPv4Network(bgp_prefix)
        bgp_address = list(net.hosts())[0]
        tvars = ncs.template.Variables()
        tvars.add('MANAGEMENT_ADDRESS', management_address)
        tvars.add('BGP_ADDRESS', bgp_address)
        template = ncs.template.Template(service)
        template.apply('loopback-template', tvars)
```

First thing that we can improve in the given code is to use a function that will calculate the management IP address and bgp address from the given prefix. With this we avoid repeating the same code for the calculation multiple times and we can also use it in the future.

The function to calculate the address from the prefix should look like this:
```python
def calculate_ip_address(prefix):
    net = ipaddress.IPv4Network(prefix)
    return str(next(net.hosts()))
```

In `the cb_create` then just call the function for the management address and the bgp address calculation:
```diff
class ServiceCallbacks(Service):
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')') # pylint: disable=protected-access

-        management_prefix = service.management_prefix
-        self.log.debug(f'Value of management-prefix leaf is {management_prefix}')
-        net = ipaddress.IPv4Network(management_prefix)
-        management_address = list(net.hosts())[0]
-
-        bgp_prefix = service.bgp_prefix
-        self.log.debug(f'Value of bgp-prefix leaf is {bgp_prefix}')
-        net = ipaddress.IPv4Network(bgp_prefix)
-        bgp_address = list(net.hosts())[0]
 
+        management_address = calculate_ip_address(service.management_prefix)
+        bgp_address = calculate_ip_address(service.bgp_prefix)
        tvars = ncs.template.Variables()
        tvars.add('MANAGEMENT_ADDRESS', management_address)
        tvars.add('BGP_ADDRESS', bgp_address)
        template = ncs.template.Template(service)
        template.apply('loopback-template', tvars)


+def calculate_ip_address(prefix):
+    net = ipaddress.IPv4Network(prefix)
+    return str(next(net.hosts()))
```

Another problem with the code is incorrect usage of the ipaddress library. Currently we are generating a list of all the host addresses that exists for give prefix. This is time and space consuming. In the terminal tab enter `python3` to enter Python terminal and type in the following snippet. Press enter and observe how long does it take for the address to be returned:
```
python3
import ipaddress
net = ipaddress.IPv4Network('10.0.0.0/8')
list(net.hosts())[0]          
```

Output:
```
developer:~ > python3
Python 3.11.2 (main, Jun 28 2023, 12:00:22) [GCC 8.5.0 20210514 (Red Hat 8.5.0-18)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import ipaddress
>>> net = ipaddress.IPv4Network('10.0.0.0/8')
>>> list(net.hosts())[0]          
IPv4Address('10.0.0.1')
>>> 
```
It takes more than 10 seconds to get the IP address back since in the background Python is creating a list of more than 16 milion addresses. It gets even worse for IPv6 ranges. Such long calculations in the `cb_create` will significantly impact performance and throughput of the NSO system.

The better way to get the first usable host address is to read just the next IP address from the generator that the library creates when you instantiate a new network object. Test the following snippet:
```
net = ipaddress.IPv4Network('10.0.0.0/8')
next(net.hosts())        
```
Output:
```
>>> net = ipaddress.IPv4Network('10.0.0.0/8')
>>> next(net.hosts())        
IPv4Address('10.0.0.1')
```
The response now is almost instant. The final version of the refactored code should look like this:

```python
class ServiceCallbacks(Service):
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')') # pylint: disable=protected-access

        management_address = calculate_ip_address(service.management_prefix)
        bgp_address = calculate_ip_address(service.bgp_prefix)
        tvars = ncs.template.Variables()
        tvars.add('MANAGEMENT_ADDRESS', management_address)
        tvars.add('BGP_ADDRESS', bgp_address)
        template = ncs.template.Template(service)
        template.apply('loopback-template', tvars)


def calculate_ip_address(prefix):
    net = ipaddress.IPv4Network(prefix)
    return str(next(net.hosts()))
```

Make sure that the final version of the `~/src/loopback/python/loopback/loopback.py` looks like the snippet above since you will use this version of the code to implement unit tests.

# Use interactive Python terminal to speed up prototyping

Often during NSO development you need to test how some Python code works on the actual NSO CDB data. Doing this through the actual service code change requires that you reload or re-deploy the package which takes time and it increases the duration of the development feedback loop.

You can use Python terminal on your NSO server and connect to the CDB through MAAPI session. By creating a maagic object you get the access to the CDB in the same way as from the `cb_create` in a service. Enter interactive Python terminal and use the following Python code:
```
python3
import ncs  
m = ncs.maapi.Maapi()  
m.start_user_session('admin', 'system', [])  
trans = m.start_write_trans()  
root = ncs.maagic.get_root(trans)
```
Output:
```
developer:~ > python3
Python 3.11.2 (main, Jun 28 2023, 12:00:22) [GCC 8.5.0 20210514 (Red Hat 8.5.0-18)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import ncs  
m = ncs.maapi.Maapi()  
m.start_user_session('admin', 'system', [])  
trans = m.start_write_trans()  
root = ncs.maagic.get_root(trans)
```

Through the `root` object you now have read write access to the CDB. The following example shows how to create device authgroup:

```
import ncs  
m = ncs.maapi.Maapi()  
m.start_user_session('admin', 'system', [])  
trans = m.start_write_trans()  
root = ncs.maagic.get_root(trans)
root.ncs__devices.authgroups.group.create('test')
root.ncs__devices.authgroups.group['test'].default_map.create()
root.ncs__devices.authgroups.group['test'].default_map.same_user.create()
root.ncs__devices.authgroups.group['test'].default_map.same_pass.create()
trans.apply()
```

Exit interactive Python terminal with `Ctrl + d`. Now you can check configuration through NSO CLI and you will see that the `test` authgroup has been created.
```
ncs_cli -C -u admin
show running-config devices authgroups
```
Output:
```
developer:~ > ncs_cli -C -u admin

User admin last logged in 2023-09-20T11:57:17.670114+00:00, to devpod-7293941003772680233-7d74554b96-l2p9g, from 127.0.0.1 using cli-console
admin connected from 127.0.0.1 using console on devpod-7293941003772680233-7d74554b96-l2p9g
admin@ncs# show running-config devices authgroups 
devices authgroups group test
 default-map same-user
 default-map same-pass
!
admin@ncs# 
```

If you need help with the Python maagic data access you can use the CLI tool to generate the code for you. First enable devtools in the NSO CLI:
```
ncs_cli -C -u admin
devtools true
```
Output:
```
developer:~ > ncs_cli -C -u admin

User admin last logged in 2023-09-20T11:57:17.670114+00:00, to devpod-7293941003772680233-7d74554b96-l2p9g, from 127.0.0.1 using cli-console
admin connected from 127.0.0.1 using console on devpod-7293941003772680233-7d74554b96-l2p9g
admin@ncs# devtools true
```

Then do the configuration that you want to do through maagic API. Instead of commit use the `show configuration | display maagic` command. To continue with the authgroup example you would do:
```
config
devices authgroups group test2 default-map same-user same-pass
top
show configuration | display maagic 
```
Output:
```
admin@ncs(config)# devices authgroups group test default-map same-user same-pass
admin@ncs(config)# top
admin@ncs(config)# show configuration | display maagic 
root = ncs.maagic.get_root(t)
root.ncs__devices.authgroups.group.create('test2')
root.ncs__devices.authgroups.group['test2'].default-map.create()
root.ncs__devices.authgroups.group['test2'].default-map.same-user.create()
root.ncs__devices.authgroups.group['test2'].default-map.same-pass.create()
```

Note that there is a minor bug so some dashes (`-`) need to be replaced with underscores (`_`). Make sure that you use different group name (one that does not exist yet) otherwise NSO will figure out that group already exists and it will not show the Python code to create it.

Exit NSO CLI:
```
admin@ncs(config)# exit
admin@ncs# exit
```

# Testing

Testing is a critical and fundamental aspect of software development that plays an important role in ensuring the reliability, functionality, and overall quality of a software product. Testing in software development involves various approaches and levels to ensure that software works as intended. In the following example you will learn how to unit test the function that you have refactored for calculating ip addresses and how to automatically run it as part of service package build procedure. 

As with Pylint, with this approach unit tests will be executed as part of a build job. If you are building your packages as part of a CI job the test will be executed in the CI too.

Another example will show how you can run and do the functional test of the service package that stores expected device configuration and compares it with the expected output.

## Unit testing

Write a unit test for the `calculate_ip_address` function. Start by creating a new folder `tests` inside a python folder of the loopback package. Then create a file inside called `test_loopback.py`. 

```
mkdir ~/src/loopback/python/tests
touch ~/src/loopback/python/tests/test_loopback.py
touch ~/src/loopback/python/tests/__init__.py
```

> Note: The \_\_init\_\_.py file is needed so that `test_loopback.py` file is recognized by unittest library as Python module.

You will use Python built-in Unit test library to implement a unit test that will check if function works correctly and returns correct host address for a given prefix. Add the following code to the created file `test_loopback.py`:

```python
import unittest
from loopback.loopback import calculate_ip_address

class TestLoopbackService(unittest.TestCase):
    def test_calculate_ip_address(self):
        self.assertEqual('10.0.0.1', calculate_ip_address('10.0.0.0/24'))
        self.assertEqual('192.168.10.1', calculate_ip_address('192.168.10.0/24'))
```

Execute the unit test by running the following command from the `~/src/loopback/src` directory:

```
cd ~/src/loopback/src/
python -m unittest discover --start-directory ../python/tests --top-level-directory ../python
```

Output:
```
developer:~ > cd ~/src/loopback/src/
developer:src > python -m unittest discover --start-directory ../python/tests --top-level-directory ../python
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

Open the `Makefile` in the loopback package and add the `test` target as dependency to the `all` target. Then add the `test` target that should execute the `unittest` you manually executed before.

```
all: fxs pylint test

...

test:
    developer:src > python -m unittest discover --start-directory ../python/tests --top-level-directory ../python
```

Now every time that you will build the `loopback` package the unit tests will be executed as well. This is useful since it ensures that any changes to the Python code that might break the `calculate_ip_address` function will be detected during package build. 

Execute the following command to build the loopback package with unit testing included:
```
make -C ~/src/loopback/src all
```
Output:
```
developer:src > make -C ~/src/loopback/src all
make: Entering directory '/home/developer/src/loopback/src'
python -m unittest discover --start-directory ../python/tests --top-level-directory ../python
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
make: Leaving directory '/home/developer/src/loopback/src'
```

## System testing and storing expected configuration

In the following section you will implement a system test for the `loopback` package. This will test that the package successfully loads into the NSO and that you can create device configurations with it. For better control over the produced device configuration you will also implement saving of the device configuration after each test run and comparing it with the expected configuration.

The idea behind this is that you inspect the configuration that loopback package creates for the given output and save it in the `expected_configuration` directory. After each test run you save the configuration into `output` directory and the compare `output` of a current test run with the known `expected_configuration`. 

This ensures that there are no unwanted configuration changes that would be result of a bad code or template change. If the change is expected you update the `expected_configuration` and the test will pass again.

Start by creating a netsim device that you will configure with loopback interfaces in the test. Create new folder `test` and use `ncs-netsim` command to add a ios-xr device to it.

```
mkdir ~/src/test
cd ~/src/test
ncs-netsim create-device $NCS_DIR/packages/neds/cisco-iosxr-cli-3.5/ core-router
```
Output:
```
developer:src > mkdir ~/src/test
developer:src > cd ~/src/test
developer:test > ncs-netsim create-device $NCS_DIR/packages/neds/cisco-iosxr-cli-3.5/ core-router
DEVICE core-router CREATED
```

You will use `Make` automation tool for test automation that you are already familiar with from the package build process. 

Start by creating a `Makefile` file in the `test` folder.
```
touch ~/src/test/Makefile
```

 Add the following `start` target to the created `Makefile` that will start the generated netsim device:
```
start:
	ncs-netsim --dir netsim stop
	ncs-netsim --dir netsim start
```

> Note: You need to use tabs as a delimiter in Makefiles, not spaces. If you get an error when running Makefile with make command make sure that there are no spaces used as delimiters. You can convert spaces to tabs using VSCode. On the bottom right line there is `Spaces: 4` text you can click on. In the dropdown menu that will open select `Convert Indentation to Tabs` option.

A good practice is to write the targets in an immutable manner - here we are always first stopping the netsim device to avoid failures when device would be already started.

Continue by copying the loopback package to the NSO running directory. Also copy iosxr-cli-3.5 NED from the installation directory.
```
cp -r ~/src/loopback $NCS_RUN_DIR/packages/
cp -r $NCS_DIR/packages/neds/cisco-iosxr-cli-3.5 $NCS_RUN_DIR/packages/
```

Enter the NSO CLI and execute packages reload command.
```
ncs_cli -C -u admin
packages reload
```
Output:
```
developer:src > ncs_cli -C -u admin

User admin last logged in 2023-10-09T05:48:46.970494+00:00, to devpod-7429870700027285884-69f76849db-jhgcg, from 127.0.0.1 using cli-console
admin connected from 127.0.0.1 using console on devpod-7429870700027285884-69f76849db-jhgcg
admin@ncs# packages reload

>>> System upgrade is starting.
>>> Sessions in configure mode must exit to operational mode.
>>> No configuration changes can be performed until upgrade has completed.
>>> System upgrade has completed successfully.
reload-result {
    package cisco-iosxr-cli-3.5
    result true
}
reload-result {
    package loopback
    result true
}
admin@ncs# 
```
Exit NSO CLI.
```
admin@ncs# exit
```

In the `test` directory run the following command:
```
cd ~/src/test
ncs-netsim ncs-xml-init > core-router.xml
```

This will create a `core-router.xml` file that contains the NSO configuration for the netsim device.

Continue by adding a target `add-device:` into the test Makefile:

```
add-device:
	echo -e "config\n devices authgroup group default default-map remote-name admin remote-password admin\ncommit\n" | ncs_cli -C -u admin
	ncs_load -m -l core-router.xml
```

This will create the authgroup and apply the configuration for the `core-router` device that is in the generated XML file.

The next step is to prepare device to be configured by the NSO. You need to fetch SSH keys and sync configuration from the device. Under `add-device` target add the following commands:
```
add-device:
	echo -e "config\n devices authgroup group default default-map remote-name admin remote-password admin\ncommit\n" | ncs_cli -C -u admin
	ncs_load -m -l core-router.xml
	echo "devices fetch-ssh-host-keys" | ncs_cli -C -u admin
	echo "devices device core-router sync-from" | ncs_cli -C -u admin
```

Now add the `configure-loopback` target that will be used to create sample loopback configuration:

```
configure-loopback:
	echo -e "config\nloopback test device core-router management-intf 1 management-prefix 10.0.0.0/24 bgp-intf 2 bgp-prefix 192.168.0.0/24\ncommit\n" | ncs_cli -C -u admin
```

The `remove-loopback` target will be used so that you can execute the test multiple times - it makes sure that loopback service code is always executed.
```
remove-loopback:
	echo -e "config\n no loopback\ncommit\n" | ncs_cli -C -u admin
```

Create two folders in `test`: `expected` to store configuration that is examined and tested, and `output` where configuration after each test execution is stored.
```
mkdir ~/src/test/expected
mkdir ~/src/test/output
```

To the `Makefile` add `save-output` target that will store the device configuration from the NSO to the `output/device-loopback.xml` file.
```
save-output:
	ncs_load -P "/devices/device[name='core-router']/config" -F p > output/device-loopback.xml
```

Another target you will need is `check-diff` that will make sure that output and expected configurations match. Otherwise `make` will fail and diff will be displayed.
```
check-diff:
	diff -c expected/ output/
```

The `test` and `all` targets are there to execute multiple commands. Add them to Makefile:
```
test:
	$(MAKE) remove-loopback
	$(MAKE) configure-loopback
	$(MAKE) save-output
	$(MAKE) check-diff

all:
	$(MAKE) start
	$(MAKE) add-device
	$(MAKE) test
```

The final `Makefile` should look like this:
```
start:
	ncs-netsim --dir netsim stop
	ncs-netsim --dir netsim start

add-device:
	echo -e "config\n devices authgroup group default default-map remote-name admin remote-password admin\ncommit\n" | ncs_cli -C -u admin
	ncs_load -m -l core-router.xml
	echo "devices fetch-ssh-host-keys" | ncs_cli -C -u admin
	echo "devices device core-router sync-from" | ncs_cli -C -u admin

configure-loopback:
	echo -e "config\nloopback test device core-router management-intf 1 management-prefix 10.0.0.0/24 bgp-intf 2 bgp-prefix 192.168.0.0/24\ncommit\n" | ncs_cli -C -u admin

remove-loopback:
	echo -e "config\n no loopback\ncommit\n" | ncs_cli -C -u admin

save-output:
	ncs_load -P "/devices/device[name='core-router']/config" -F p > output/device-loopback.xml

check-diff:
	diff -c expected/ output/

test:
    $(MAKE) remove-loopback
    $(MAKE) configure-loopback
    $(MAKE) save-output
    $(MAKE) check-diff

all:
	$(MAKE) start
	$(MAKE) add-device
	$(MAKE) test
```

Now invoke the `all` target to start the netsim device, configure NSO with prerequisite configuration and test the package:
```
make -C ~/src/test all
```

Output:
```
developer:test > make -C ~/src/test all
make start
make[1]: Entering directory '/home/developer/src/test'
ncs-netsim --dir netsim stop
DEVICE core-router STOPPED
ncs-netsim --dir netsim start
DEVICE core-router OK STARTED
make[1]: Leaving directory '/home/developer/src/test'
make add-device
make[1]: Entering directory '/home/developer/src/test'
echo -e "config\n devices authgroup group default default-map remote-name admin remote-password admin\ncommit\n" | ncs_cli -C -u admin
Commit complete.
ncs_load -m -l core-router.xml
echo "devices fetch-ssh-host-keys" | ncs_cli -C -u admin
fetch-result {
    device core-router
    result unchanged
    fingerprint {
        algorithm ssh-ed25519
        value 11:5e:be:6c:b1:22:b3:f6:24:2a:10:31:dd:ad:8e:c4
    }
    fingerprint {
        algorithm ssh-rsa
        value c0:80:68:f8:f3:5c:09:7d:c8:05:3f:a1:3d:c8:cb:8c
    }
}
echo "devices device core-router sync-from" | ncs_cli -C -u ad
result true
make[1]: Leaving directory '/home/developer/src/test'
make test
make[1]: Entering directory '/home/developer/src/test'
make configure-loopback
make[2]: Entering directory '/home/developer/src/test'
echo -e "config\nloopback test device core-router management-intf 1 management-prefix 10.0.0.0/24 bgp-intf 2 bgp-prefix 192.168.0.0/24\ncommit\n" | ncs_cli -C -u admin
Commit complete.
make[2]: Leaving directory '/home/developer/src/test'
make save-output
make[2]: Entering directory '/home/developer/src/test'
ncs_load -P "/devices/device[name='core-router']/config" -F p > output/device-loopback.xml
make[2]: Leaving directory '/home/developer/src/test'
make check-diff
make[2]: Entering directory '/home/developer/src/test'
diff -c expected/ output/
Only in output/: device-loopback.xml
make[2]: *** [Makefile:18: check-diff] Error 1
make[2]: Leaving directory '/home/developer/src/test'
make[1]: *** [Makefile:23: test] Error 2
make[1]: Leaving directory '/home/developer/src/test'
make: *** [Makefile:28: all] Error 2
developer:test > 
```

As you can see the whole test flow was executed with a single `make` command. But the test was not successful. You can see that target that checks the diff between output and expected output failed. The reason for this is that you need to create
the expected file - you can do so by examining and copying the file `~/src/test/output/device-loopback.xml` created in the output directory. Open and study the output file in the editor. Alternatively, you can check the file through the terminal:
```
cat ~/src/test/output/device-loopback.xml
```

After you make sure that this is the expected configuration created by loopback package copy it over to `expected` directory:
```
cp ~/src/test/output/device-loopback.xml expected/
```

Execute the test again. This time you can only execute the `test` target since test environment is already running:
```
make -C ~/src/test test
```
Output:
```
developer:test > make test
make configure-loopback
make[1]: Entering directory '/home/developer/src/test'
echo -e "config\nloopback test device core-router management-intf 1 management-prefix 10.0.0.0/24 bgp-intf 2 bgp-prefix 192.168.0.0/24\ncommit\n" | ncs_cli -C -u admin
% No modifications to commit.
make[1]: Leaving directory '/home/developer/src/test'
make save-output
make[1]: Entering directory '/home/developer/src/test'
ncs_load -P "/devices/device[name='core-router']/config" -F p > output/device-loopback.xml
make[1]: Leaving directory '/home/developer/src/test'
make check-diff
make[1]: Entering directory '/home/developer/src/test'
diff -c expected/ output/
make[1]: Leaving directory '/home/developer/src/test'
developer:test > 
```

There is no difference between the files and the test was successful. To see how `check-diff` detects unintended changes to the configuration break the `loopback-template.xml` file on purpose. Open the `~/src/loopback/templates/loopback-template.xml` file in the editor and remove the line 21:
```diff
			  <Loopback>
               <id>{/bgp-intf}</id>
               <ipv4>
                 <address>
                   <ip>{$BGP_ADDRESS}</ip>
-                   <mask>255.255.255.255</mask>
                 </address>
               </ipv4>
             </Loopback>
           </interface>
```

This will create the bgp loopback interface without the mask. Copy changed file to NSO running directory:
```
cp ~/src/loopback/templates/loopback-template.xml $NCS_RUN_DIR/packages/loopback/templates/
```
Output:
```
developer:src > cp ~/src/loopback/templates/loopback-template.xml $NCS_RUN_DIR/packages/loopback/templates/
```

Enter NSO CLI and redeploy the loopback package:
```
ncs_cli -C -u admin
packages package loopback redeploy
exit
```
Output:
```
developer:src > ncs_cli -C -u admin

User admin last logged in 2023-10-13T11:34:40.601179+00:00, to devpod-7430150751460313849-6b75d9874-c8gvn, from 127.0.0.1 using cli-console
admin connected from 127.0.0.1 using console on devpod-7430150751460313849-6b75d9874-c8gvn
admin@ncs# packages package loopback redeploy 
result true
admin@ncs#
admin@ncs# exit 
```
> Note: Since you only changed the template it is enough to just redeploy a package. When you are changing YANG model of a package then full packages reload is needed, which takes longer especially with big models. 

Now execute the test target again and observe the output:
```
make -C ~/src/test test
```
Output:
```
developer:test > make test
make remove-loopback
make[1]: Entering directory '/home/developer/src/test'
echo -e "config\n no loopback\ncommit\n" | ncs_cli -C -u admin
% No modifications to commit.
make[1]: Leaving directory '/home/developer/src/test'
make configure-loopback
make[1]: Entering directory '/home/developer/src/test'
echo -e "config\nloopback test device core-router management-intf 1 management-prefix 10.0.0.0/24 bgp-intf 2 bgp-prefix 192.168.0.0/24\ncommit\n" | ncs_cli -C -u admin
Commit complete.
make[1]: Leaving directory '/home/developer/src/test'
make save-output
make[1]: Entering directory '/home/developer/src/test'
ncs_load -P "/devices/device[name='core-router']/config" -F p > output/device-loopback.xml
make[1]: Leaving directory '/home/developer/src/test'
make check-diff
make[1]: Entering directory '/home/developer/src/test'
diff -c expected/ output/
diff -c expected/device-loopback.xml output/device-loopback.xml
*** expected/device-loopback.xml        2023-10-13 11:32:25.373773316 +0000
--- output/device-loopback.xml  2023-10-13 11:58:00.923751692 +0000
***************
*** 18,24 ****
              <ipv4>
                <address>
                  <ip>192.168.0.1</ip>
-                 <mask>255.255.255.255</mask>
                </address>
              </ipv4>
            </Loopback>
--- 18,23 ----
make[1]: *** [Makefile:21: check-diff] Error 1
make[1]: Leaving directory '/home/developer/src/test'
make: *** [Makefile:27: test] Error 2
developer:test > 
```

As you can see in the output our target detected that `mask` is not configured anymore and the `test` target failed.

You have successfully finished the lab.

Visit https://developer.cisco.com/site/nso/#directory-developer for more labs on NSO Service Development.

To learn more about GNU Make used in this lab visit https://www.gnu.org/software/make/manual/make.html

For Python unit test library documentation visit https://docs.python.org/3/library/unittest.html
