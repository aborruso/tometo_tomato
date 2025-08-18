This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: src/**/*.md
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
src/
  advanced/
    bash-completion.md
    erb-in-config.md
    extensible-scripts.md
    filters.md
    hooks.md
    lib-source.md
    library.md
    rendering.md
    split-config.md
    strings.md
    validations.md
  configuration/
    argument.md
    command.md
    dependency.md
    environment-variable.md
    flag.md
    variable.md
  usage/
    getting-started.md
    settings.md
    testing-your-scripts.md
    writing-your-scripts.md
  demo.md
  examples.md
  index.md
  installation.md
  installing-ruby.md
```

# Files

## File: src/advanced/bash-completion.md
`````markdown
---
icon: dot
order: 60
---

# Bash Completion

Bashly comes with a built-in bash completions generator, provided by the
[completely][completely] gem.

By running `bashly add completions`, you can add this functionality to your
script in one of three ways:


==- `bashly add completions`
Creates a function in your `./src/lib` directory that echoes a completion
script. You can then call this function from any command (for example `yourcli
completions`) and your users will be able to install the completions by running
`eval "$(yourcli completions)"`.

==- `bashly add completions_script`
Creates a standalone completions script that can be sourced or copied to the
system's bash completions directory.

==- `bashly add completions_yaml`
Creates the raw data YAML file. This is intended mainly for development
purposes.

===

The bash completions generation is **completely automatic**, but you will have
to regenerate the completion function whenever you make changes to your
`bashly.yml` file. 

!!!success Tip
By running `bashly generate --upgrade`, your completions function 
(generated with `bashly add completions`) will be regenerated.
!!!

## Custom command completions

In addition to the automatic suggestion of subcommands and flags, you can
instruct bashly to also suggest files, directories, users, git branches and
more. To do this, add another option in your `bashly.yml` on the command you
wish to alter:

```yaml bashly.yml
commands:
- name: upload
  help: Upload a file
  completions:
  - <directory>
  - <user>
  - $(git branch 2> /dev/null)

```

## Custom flag completions

The `completions` option is also available on flags that have an `arg`.
Similarly to the `allowed` option for arguments, the allowed list is added
to the suggestions automatically (without the need to use `completions`).

```yaml bashly.yml
commands:
- name: login
  help: Login to SETI
  flags:
  - long: --user
    arg: username
    completions:
    - <user>
  - long: --protocol
    arg: protocol
    allowed:
      - ssh
      - telnet
```

- Anything between `<...>` will be added using the `compgen -A action` flag.
- Anything else, will be appended to the `compgen -W` flag.

!!! Note
In case you are using the
[Argument `allowed` option](../configuration/argument.md#allowed) or 
the [Flag argument `allowed` option](../configuration/flag.md#allowed),
these will be automatically added to the completions list as well.
!!!

## Completions in ZSH

If you are using Oh-My-Zsh, bash completions should already be enabled,
otherwise, you should enable completion by adding this to your `~/.zshrc`
(if it is not already there):

```bash
# Load completion functions
autoload -Uz +X compinit && compinit
autoload -Uz +X bashcompinit && bashcompinit
```

After adding this (and restarting your session), you should be able to source
any bash completion script in zsh.

## Additional documentation

For more information about these custom completions, see the
[documentation for the completely gem][completely-docs].

## Example

[!button variant="primary" icon="code-review" text="Bash Completions Example"](https://github.com/bashly-framework/bashly/tree/master/examples/completions#readme)


[completely]: https://github.com/DannyBen/completely
[completely-docs]: https://github.com/DannyBen/completely#suggesting-files-directories-and-other-bash-built-ins
[compgen]: https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion-Builtins.html
`````

## File: src/advanced/erb-in-config.md
`````markdown
---
icon: dot
order: 45
---

# ERB in Config

The `bashly.yml` configuration is pre-processed by ERB before it is loaded
by the bashly command line. This means that you can use Ruby code to load
values from external sources into your bashly configuration.

- Use `<%= ... %>` to execute Ruby code and output the result.
- Use `<% ... %>` to execute Ruby code without outputting the result.
`````

## File: src/advanced/extensible-scripts.md
`````markdown
---
icon: dot
order: 40
---

# Extensible Scripts

You may configure your generated bash script to delegate any unknown command to an external executable, by setting the `extensible` option to either `true`, or to a different external command.

This is similar to how `git` works. When you execute `git whatever`, the `git` command will look for a file named `git-whatever` in the path, and execute it.

!!! Note
The `extensible` option cannot be specified together with the `default` option,
since both specify a handler for unknown commands.
!!!

The `extensible` option supports two operation modes:

## Extension mode

`extensible: true`

By setting `extensible` to `true`, a specially named executable will be called when an unknown command is called by the user.

Given this configuration:

```yaml bashly.yml
name: myscript
help: Example
version: 0.1.0
extensible: true

commands:
- name: upload
  help: Upload a file
```

And this user command:

```shell
$ myscript something

```

The generated script will look for an executable named `myscript-something` in the path. If found, it will be called.

[!button variant="primary" icon="code-review" text="Extensible Extension Example"](https://github.com/bashly-framework/bashly/tree/master/examples/extensible#readme)

## Delegate mode

`extensible: <executable name>`

By setting `extensible` to any string, unknown command calls by the user will be delegated to the executable with that name.

Given this configuration:

```yaml bashly.yml
name: mygit
help: Example
version: 0.1.0
extensible: git

commands:
- name: push
  help: Push to my repository
```

And this user command:

```shell
$ mygit status

```

The generated script will execute `git status`.

[!button variant="primary" icon="code-review" text="Extensible Delegate Example"](https://github.com/bashly-framework/bashly/tree/master/examples/extensible-delegate#readme)
`````

## File: src/advanced/filters.md
`````markdown
---
icon: dot
order: 70
---

# Custom Filters

Bashly supports custom filter functions for your commands. These filters allow
you to define custom conditions that can prevent your command from running
unless they are met.

This is how it works:

1. In your Bashly configuration file, commands can include a `filters` option,
   which specifies an array of one or more function names.
2. Whenever you run your script, it will search for functions with those names,
   prefixed by `filter_`, and execute them before running the command code.
3. If any of the functions return (echo) a string, it will be treated as an
   error. The returned string will be displayed on the screen as the error message.


+++ Configuration

```yaml bashly.yml
name: viewer
filters:
- docker_running
```

+++ Custom Function

```shell src/lib/filter_docker_running.sh
filter_docker_running() {
  docker info > /dev/null 2>&1 || echo "Docker must be running"
}
```

+++

[!button variant="primary" icon="code-review" text="Filters Example"](https://github.com/bashly-framework/bashly/tree/master/examples/filters#readme)

!!!success Tips
- To verify a program is installed, use [`dependencies`](/configuration/command/#dependencies) instead.
- To verify an environment variable is defined, use [`environment_variables`](/configuration/command/#environment_variables) instead.
!!!
`````

## File: src/advanced/hooks.md
`````markdown
---
icon: dot
order: 65
---

# Function Hooks

Bashly provides you with three general purpose hooks that let you inject your
own code. To use a hook, simply create one of the files listed below in your
`src` directory.

!!!success Tip
Run `bashly add hooks` to create the hook files in your source directory.
!!!

## Hook Files


### `src/initialize.sh`

Execute code inside the `initialize()` function, which is called before anything
else. The `command_line_args` array is available to you here, allowing you to
read or modify (not recommended) the input command line.

### `src/before.sh`

Execute code before calling any command, but after processing the command line
input. The `args` and `extra_args` arrays are available to you here, as well as
the `input` array, which contains the normalized command line arguments.

### `src/after.sh`

Execute code after calling any command.

[!button variant="primary" icon="code-review" text="Hooks Example"](https://github.com/bashly-framework/bashly/tree/master/examples/hooks#readme) [!button variant="primary" icon="code-review" text="Command Line Manipulation Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-line-manipulation#readme)

## Alternatives

These hooks should be considered a last resort, for any functionality that is not
covered by more native means.

Below is a list of some related features that can
be used instead of using these hooks:

- To change bash runtime parameters (e.g. `set -o pipefail`), use the [`strict` setting](/usage/settings/#strict) instead.
- To verify a program is installed, use [`dependencies`](/configuration/command/#dependencies) instead.
- To verify an environment variable is defined, use [`environment_variables`](/configuration/command/#environment_variables) instead.
- To perform validation operations, use [Custom Validations](/advanced/validations/) instead.
- To halt the execution of the command unless certain conditions are met, use [Custom Filters](/advanced/filters/) instead.
`````

## File: src/advanced/lib-source.md
`````markdown
---
icon: dot
order: 30
---

# Custom Libraries Source

## Overview

Bashly is capable of importing external library functions from a custom central
libraries source using the `bashly add --source NAME ...` command.

These external library sources can be:

1. A local path
2. A remote git repository
3. A remote GitHub repository (public or private)

This can be useful if:

1. You have multiple bashly-generated scripts, and wish to have a central place
   for shareable libraries.
2. You wish to create a public source for libraries for bashly.
3. You wish to create a private shareable libraries source for your organization.

## Specifications

The external library source must have a `libraries.yml` file describing the 
libraries it provides. A typical `libraries.yml` file looks like this:

```yaml
colors:
  help: Add standard functions for printing colorful text.
  files:
    - source: "colors/colors.sh"
      target: "%{user_lib_dir}/colors.%{user_ext}"

config:
  help: Add standard functions for handling INI files.
  files:
    - source: "config/config.sh"
      target: "%{user_lib_dir}/config.%{user_ext}"

  post_install_message: |
    Remember to set up the CONFIG_FILE variable in your script.
    For example: CONFIG_FILE=settings.ini.
```

### `help`

The message to show when running `bashly add --source NAME --list`

### `files`

An array of `source` + `target` paths of files to copy when adding this library.

- `source` is relative to the root of the library source.
- `target` is relative to the current directory, and you can use any of these
  tokens in the path:
  - `%{user_source_dir}` - path to the user's source directory (normally `./src`).
  - `%{user_target_dir}` - path to the user's target directory (normally `.`).
  - `%{user_lib_dir}` - path to the user's `lib` directory (normally `./src/lib`).
  - `%{user_ext}` - the user's selected partials extension (normally `sh`).

### `post_install_message`

An optional message to show after the user installs the library. You can use a 
multi-line YAML string here, and use color markers as specified by the
[Colsole](https://github.com/dannyben/colsole#colors) gem. 

In the below example, ``g`...` `` means green, ``m`...` `` magenta, and 
``bu`...` `` blue underlined:

```yaml
post_install_message: |
  Edit your tests in g`test/approve` and then run:

    m`$ test/approve`

  Docs: bu`https://github.com/DannyBen/approvals.bash`
```

## Auto-upgrade

Your library files can be set to auto-upgrade when running
`bashly generate --upgrade`. In order to enable this functionality, you need to 
add a special upgrade marker to your file:

```bash
## [@bashly-upgrade source-uri;library-name]
```

For example

```bash
## [@bashly-upgrade github:you/your-repo;config]
```

You can also use the shorthand version of the marker, which will be replaced
with the full marker when the library is added:

```bash
## [@bashly-upgrade]
```

The double-hash comment marker is optional, and denotes a
[hidden comment](/usage/writing-your-scripts/#hidden-comments), which will not
appear in the final generated bash script.
`````

## File: src/advanced/library.md
`````markdown
---
icon: dot
order: 90
---

# Library Functions

Bashly comes with a set of library functions that can be added to your script
by running the `bashly add` command. All libraries are documented inline, and
the documentation below is a high level overview with examples.

!!!success Tip
Run `bashly add --list` to see all available libraries.
!!!



## YAML parser

Adds the ability to read YAML files in your bash script.

```bash
$ bashly add yaml
````

==- :icon-code-review: Usage Example

```bash
yaml_load "settings.yml"             # print variables
yaml_load "settings.yml" "config_"   # use prefix
eval $(yaml_load "settings.yml")     # create variables in scope
````

[!button variant="primary" icon="code-review" text="YAML Example on GitHub"](https://github.com/bashly-framework/bashly/tree/master/examples/yaml#readme)

===



## Config (INI) handler

Adds the ability to create, read and write configuration INI files. This library
uses the [ini library](#ini-handler) under the hood for loading and saving the
INI files.

```bash
$ bashly add config
```

==- :icon-code-review: Usage Example

```bash
# Add or update a key=value pair in the config.
config_set username Operations

# Use dot notation to specify an INI section ([login] in this case).
config_set login.email paul@section.one

# Get the value from the config file.
result=$(config_get login.username)

# Delete a key from the config.
config_del username

# Show the config file.
config_show

# Return an array of the keys in the config file
for key in $(config_keys); do
  echo "- $key = $(config_get "$key")";
done

# Returns true if the specified key exists in the config file
if config_has_key "key" ; then
  echo "key exists"
fi
```

[!button variant="primary" icon="code-review" text="Config Example on GitHub"](https://github.com/bashly-framework/bashly/tree/master/examples/config#readme)

===



## INI handler

Adds the ability to load and save INI files. This is a low-level library that
is used by the [config library](#config-ini-handler).

```bash
$ bashly add ini
```

==- :icon-code-review: Usage Example

```bash
# Load an INI file into the `ini` associative array.
ini_load 'path/to/file.ini'

# Save the associative array back to the INI file.
ini_save 'path/to/file.ini'

# Access a value
name=${ini[key]}
name=${ini[section.key]}
name=${ini[section.key]:-default}

# Create/update a value
ini[section.key]="new value"
ini_save

# Delete a value
unset ini[section.key]
ini_save

# Show the loaded values
ini_show
```

[!button variant="primary" icon="code-review" text="INI Example"](https://github.com/bashly-framework/bashly/tree/master/examples/ini#readme)

===



## Color output

Adds functions for printing colored strings.

```bash
$ bashly add colors
```

==- :icon-code-review: Usage Example

```bash
echo "before $(red this is red) after"
echo "before $(green_bold this is green_bold) after"
```

See the generated script in `src/lib/colors.sh` for the full list of colors.

[!button variant="primary" icon="code-review" text="Colors Example"](https://github.com/bashly-framework/bashly/tree/master/examples/colors#readme)

===



## Auto-update

Files added by the `bashly add *` commands can be automatically updated to their
original state by running

```bash
bashly generate --upgrade
````

The `--upgrade` flag will scan all the files in the `src/lib` directory for a 
special magic comment in this format:

```
[@bashly-upgrade <library>]
```

When found, and assuming the path of the file matches the one in the library,
this file will be updated.

You are encouraged to modify the generated library functions to your liking, but
if you do so, remember to remove this magic comment to prevent accidentally 
overriding it in future runs of `bashly generate --upgrade`.



## See also

[!ref](/advanced/lib-source/)
`````

## File: src/advanced/rendering.md
`````markdown
---
icon: dot
order: 35
---

# Rendering Documentation

## Overview

Bashly is capable of rendering documentation for your script based on
your `bashly.yml` configuration by using the `bashly render` command.

This command can generate any kind of output using either templates that are 
built into Bashly (for example Markdown or man pages), or by using
any custom templates.

## Built-in templates

Bashly comes with several documentation templates. In order to see a list of
all templates, run:

```bash
$ bashly render --list
```

Some built-in templates may have special optional features that let you
customize the output. Learn more about each template by running:

```bash
$ bashly render SOURCE --about
# for example
$ bashly render :mandoc --about
```

## Example

[!button variant="primary" icon="code-review" text="Markdown Example"](https://github.com/bashly-framework/bashly/tree/master/examples/render-markdown#readme) [!button variant="primary" icon="code-review" text="Mandoc Example"](https://github.com/bashly-framework/bashly/tree/master/examples/render-mandoc#readme)

## Custom templates

### Create your own

To create custom templates, it is recommended to use one of the built-in
templates as a starting point. To copy the template source code to your project
run:

```bash
$ bashly add render_markdown
# or
$ bashly add render_mandoc
```

!!! Note
Creating custom templates requires some minimal understanding of Ruby.
!!!

### Template structure

Template directories are expected to:

1. Have a `render.rb` file  
   Will be executed when running `bashly render`.
2. Have a `README.md` file  
   Will be shown when running with `--about`.

The `render.rb` file will be executed when running `bashly render` and 
will have access to these variables and methods:

| Variable  | Description
|-----------|---------
| `command` | The root command of your bashly script ([`Bashly::Script::Command`](https://github.com/bashly-framework/bashly/blob/master/lib/bashly/script/command.rb)).
| `source`  | A string containing the path to the template source directory.
| `target`  | A string containing the path to the target directory, as provided by the user at run time (`bashly render SOURCE TARGET`).
| `show`    | A string that will contain the value of `--show PATH` if provided by the user at runtime.

| Method | Description
|--------|-------------
| `save` | The method your script should call in order to save an output file.
| `say`  | Print a message with colors (see [Colsole](https://github.com/dannyben/colsole))

The `render.rb` script is executed with the [`Bashly::RenderContext`](https://github.com/bashly-framework/bashly/blob/master/lib/bashly/render_context.rb) context.

### Render script example

This approach allows you to use any template engine that is available in Ruby.

For example, this `render.rb` file uses GTX to render the markdown
documentation:

```ruby render.rb
# render script - markdown
require 'gtx'

# for previewing only (not needed for rendering)
require 'tty-markdown'

# Load the GTX template
template = "#{source}/markdown.gtx"
gtx = GTX.load_file template

# Render the file for the main command
save "#{target}/index.md", gtx.parse(command)

# Render a file for each subcommand
command.deep_commands.reject(&:private).each do |subcommand|
  save "#{target}/#{subcommand.full_name}.md", gtx.parse(subcommand)
end

# Show one of the files if requested
if show
  file = "#{target}/#{show}"
  puts TTY::Markdown.parse_file(file) if File.exist?(file)
end
```

[!button variant="primary" icon="mark-github" text="See it on GitHub"](https://github.com/bashly-framework/bashly/tree/master/lib/bashly/libraries/render/markdown)

### Custom properties

The `bashly.yml` allows the use of arbitrary properties. Any property that starts with `x_` is
ignored by the validation process, and is therefore allowed.

You can use this functionality to add properties that can be used in your
rendering templates. See one of the built-in templates for usage example.
`````

## File: src/advanced/split-config.md
`````markdown
---
icon: dot
order: 50
---

# Split Config

In case your `bashly.yml` file becomes too large, you may import smaller
configuration snippets by using the `import` keyword.

Loaded configuration snippets can be placed in:

1. Other YAML files, anywhere you want (typically, inside your `src` folder).
2. As a YAML front matter, alongside the shell code that they represent.

## Importing other YAML files

Consider the below, standard `bashly.yml` config:

```yaml bashly.yml
name: cli
help: Sample application

commands:
  name: download
  alias: d
  help: Download something

  args:
  - ...
```

Extracting the `download` command to a separate YAML file, looks like this:

+++ bashly.yml

```yaml bashly.yml
name: cli
help: Sample application

commands:
- import: src/download.yml
- import: ... additional files ...

```

+++ download.yml

```yaml download.yml
name: download
alias: d
help: Download something

args:
- ...
```

+++

## Embedding the YAML definition alongside its bash code

The `import` directive can also be used to load YAML front matter from any text
file. This feature can be useful in case you wish to embed the definition of
the command alongside its source code (shell script).

+++ bashly.yml

```yaml bashly.yml
name: cli
help: Sample application

commands:
- import: src/download_command.sh

```

+++ download_command.sh

```shell download_command.sh
name: download
alias: d
help: Download a file
args:
- name: source
  required: true
  help: File to upload
---
# Your shell script starts here, after the '---' YAML marker
inspect_args

```

+++

## Debugging complex configuration

Running `bashly validate --verbose` shows the configuration file as Bashly sees
it, even if it is invalid. This can be helpful when trying to debug validation
errors for complex configuration files.

[!button variant="primary" icon="code-review" text="Split Config Example"](https://github.com/bashly-framework/bashly/tree/master/examples/split-config#readme)
`````

## File: src/advanced/strings.md
`````markdown
---
icon: dot
order: 100
---

# Custom Strings

Bashly lets you control all the strings emitted by your generated bash script.

Most of these strings (for example, help messages) are configured as part of
your `bashly.yml` configuration file.

However, if you also wish to customize other strings (for example, error
messages), you will need to add a file named `bashly-strings.yml` to your 
`src` folder.

To do so, run:

```bash
$ bashly add strings
```

This will add a configuration file with all the internal strings for you to
configure.

For example:

```yaml
flag_requires_an_argument: "%{name} requires an argument: %{usage}"
invalid_argument: "invalid argument: %s"
```

!!! Note
Some strings contain special tokens, such as `%s` and `%{name}`.
These will be replaced at runtime and you should keep them in your custom
strings.
!!!

[!button variant="primary" icon="code-review" text="Custom Strings Example"](https://github.com/bashly-framework/bashly/tree/master/examples/custom-strings#readme)
`````

## File: src/advanced/validations.md
`````markdown
---
icon: dot
order: 80
---

# Custom Validations

Bashly supports custom validation functions for your arguments, flag
arguments, and environment variables. This is how it works:

1. In your bashly configuration file, arguments and flags (with arguments)
   may have a `validate: function_name` option.
2. Whenever you run your script, it will look for a function with that name,
   prefixed by `validate_` and will run it before allowing the user
   input to pass.
3. If the function returns any string, it is considered an error. The
   string will be displayed on screen, as the error message.

+++ Configuration

```yaml bashly.yml
name: viewer

args:
- name: path
  validate: file_exists
```

+++ Custom Function

```shell src/lib/validate_file_exists.sh
validate_file_exists() {
  [[ -f "$1" ]] || echo "must be an existing file"
}
```

+++


## Built-in Custom Validations

In addition, bashly comes with several built-in custom validations for common
tasks:

- `file_exists` - Ensures that the argument points to a file.
- `dir_exists` - Ensures that the argument points to a directory.
- `integer` - Ensures that the argument is an integer.
- `not_empty` - Ensures that the argument is not empty.

In order to add these validations to your code, run:

```bash
$ bashly add validations
```

[!button variant="primary" icon="code-review" text="Validations Example"](https://github.com/bashly-framework/bashly/tree/master/examples/validations#readme)
`````

## File: src/configuration/argument.md
`````markdown
---
icon: dot
order: 90
---

# Argument

Specify positional arguments (required or optional) used by your script.

==- :icon-code-review: Show Me How
```yaml bashly.yml
args:
  - name: user
    help: AWS Username.
    required: true

  - name: role
    help: User role.
    default: admin
    allowed:
      - admin
      - guest

  - name: key
    help: Path to SSH key.
    validate: file_exists
```
===


The argument's value will be available to you as `${args[name]}` in your bash
function.

!!! Note
Most properties are optional, unless specified otherwise.
!!!


## Basic Options

### name

[!badge String]
[!badge variant="danger" text="Required"]

The name of the argument. Use lowercase letters, since it serves multiple
purposes:

- It will be capitalized in the help text.
- It will be used as the hash key in the `${args[...]}` associative bash array.


### help

[!badge String]

The message to display when using `--help`. Can have multiple lines.


## Common Options


### default

[!badge String / Array of Strings]

The value to use in case it is not provided by the user. Implies that this
argument is optional.

When using [`repeatable`](#repeatable), you may provide an array here. It will
be provided to your script as a space delimited string (similar to how it is
provided when the user inputs values).

[!button variant="primary" icon="code-review" text="Default Values Example"](https://github.com/bashly-framework/bashly/tree/master/examples/default-values#readme)


### required

[!badge Boolean]

Specify that this argument is required.

!!! Note
Once you define an optional argument (without `required: true`) then you cannot
define required arguments after it.
!!!


## Advanced Options

### allowed

[!badge Array of Strings]

Limit the allowed values to a specified whitelist. Can be used in conjunction
with [`default`](#default) or [`required`](#required).

[!button variant="primary" icon="code-review" text="Whitelist Example"](https://github.com/bashly-framework/bashly/tree/master/examples/whitelist#readme)


### repeatable

[!badge Boolean]

Specify that this argument can be provided multiple times.

The received value will be formatted as a quoted, space-delimited string which
you will need to convert to array with something like
`eval "data=(${args[path]})"`.

[!button variant="primary" icon="code-review" text="Repeatable Argument Example"](https://github.com/bashly-framework/bashly/tree/master/examples/repeatable-arg#readme)

### unique

[!badge Boolean]

Specify that the values for this `repeatable` argument must be unique.
Non-unique values will be ignored.


### validate

[!badge String]

Apply a custom validation function.

[!ref](/advanced/validations)
`````

## File: src/configuration/command.md
`````markdown
---
icon: dot
order: 100
---

# Command

The `command` object serves two purposes, it:

1. Defines the root CLI application (command).
2. Defines any nested subcommands, if any.

==- :icon-code-review: Show Me How
```yaml bashly.yml
name: rush
help: Personal package manager
version: 0.6.5

commands:
- name: add
  alias: a
  help: Register a local repository
  args:
  - name: repo
    required: true
    help: Repository name.

  - name: path
    required: true
    help: Path to the repository.

  examples:
  - rush add default ~/rush-repos/default

- name: remove
  alias: r
  help: Unregister a local repository
  args:
  - name: repo
    required: true
    help: Repository name.

  flags:
  - long: --purge
    short: -p
    help: Also remove the local directory.

  examples:
  - rush remove bobby
  - rush remove bobby --purge
```
===

Unless otherwise specified, these definitions can be used for both the root
command and subcommands (under the `commands` definition).

!!! Note
Most properties are optional, unless specified otherwise.
!!!


## Basic Options

### name

[!badge String]
[!badge variant="danger" text="Required"]

The name of the script or subcommand.


### alias

[!badge String / Array of Strings]
[!badge variant="warning" text="Subcommands Only"]

One or more additional optional names for this command. This can be used to
create a shortcut for a command, or provide alternative names for it.

This option accepts either a string, or an array of strings.

You can add `*` as a suffix, to denote a *starts with* pattern - for example:

```yaml bashly.yml
name: index
alias: i  # simple shortcut

name: download
alias: d*  # anything that starts with d

name: upload
alias: [u, push]  # upload, u and push will all run the same command
```

[!button variant="primary" icon="code-review" text="Command Aliases Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-aliases#readme)


### help

[!badge String]

The header text to display when using `--help`.

This option can have multiple lines. In this case, the first line will be used
as summary wherever appropriate.

### args

[!badge Array of Arguments]

Specify the array of positional arguments this script needs.

[!ref](argument.md)


### flags

[!badge Array of Flags]

Specify the array of option flags this script needs.

!!! Note
Flags that are defined in a command that has subcommands, are considered
"global flags", and will be available to all subcommands, in addition to any
flag defined in any of the subcommands themselves.

The [docker-like example](https://github.com/bashly-framework/bashly/tree/master/examples/docker-like#readme)
demonstrates this feature.
!!!

[!ref](flag.md)


### commands

[!badge Array of Commands]

Specify the array of commands. Each command will have its own args and flags.

!!! Note
Using `commands` on a given command implies that this command does not have flags or args.
!!!

[!button variant="primary" icon="code-review" text="Commands Example"](https://github.com/bashly-framework/bashly/tree/master/examples/commands#readme) [!button variant="primary" icon="code-review" text="Subcommands Example"](https://github.com/bashly-framework/bashly/tree/master/examples/commands-nested#readme) 



### version

[!badge String]
[!badge variant="warning" text="Root Command Only"]

The string to display when using `--version`.



## Common Options


### default

[!badge Boolean / String]
[!badge variant="warning" text="Subcommands Only"]

- Setting this to `true` on any command, will cause any **unrecognized**
  command line to be passed to this command.
- Setting this to `force` will also execute this command (instead of showing
  the root usage text) when executed without any arguments.

[!button variant="primary" icon="code-review" text="Default Command Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-default#readme) [!button variant="primary" icon="code-review" text="Forced Command Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-default-force#readme)


### environment_variables

[!badge Array of Environment Variables]

Specify an array of environment variables required or desired by your script. 

[!ref](environment-variable.md)


### examples

[!badge String / Array of Strings]

Specify an array of examples to show when using `--help`, or a multi-line
string. 

[!button variant="primary" icon="code-review" text="Command Examples Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-examples#readme)

### footer

[!badge String]

Add a custom message that will be displayed at the end of the `--help` text. 

[!button variant="primary" icon="code-review" text="Footer Example"](https://github.com/bashly-framework/bashly/tree/master/examples/footer#readme)


### group

[!badge String]
[!badge variant="warning" text="Subcommands Only"]

In case you have many commands, use this option to specify a caption to display
before this command.

This option is purely for display purposes.

[!button variant="primary" icon="code-review" text="Command Groups Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-groups#readme)

### variables

[!badge Array of Variables]

Specify an array of variables that can be accessed globally in your script, or subcommands.

[!ref](variable.md)

## Advanced Options

### catch_all

[!badge Boolean / String / Hash]

Specify that this command should allow for additional arbitrary arguments or
flags.

It can be set in one of three ways:

- Set to `true` to just enable it.
- Set to a string, to show this string in the usage help text.
- Set to a hash containing `label`, `help` and `required` keys, to show a
  detailed help for it when running with `--help`. By default, `catch_all`
  arguments are optional, but you can specify `required: true` to require at
  least one argument.

To access arguments captured by `catch_all` in your script, use the
`$other_args` array (or call the `inspect_args` command to see them).

[!button variant="primary" icon="code-review" text="Catch All Example"](https://github.com/bashly-framework/bashly/tree/master/examples/catch-all#readme) [!button variant="primary" icon="code-review" text="Catch All Advanced Example"](https://github.com/bashly-framework/bashly/tree/master/examples/catch-all-advanced#readme)


### completions

[!badge Array of Strings]

Specify an array of additional completion suggestions when used in conjunction
with `bashly add completions`.

[!ref](/advanced/bash-completion.md)


### dependencies

[!badge Array of Strings / Hash / Array of Dependencies]

Specify a list of required external dependencies (commands) required by your
script.

[!ref](dependency.md)

### help_header_override

[!badge String]

Provide an alternative bash code or function call to be executed at the start of
the help message. This is useful for displaying ASCII art when running your CLI
with the `--help` option.

[!button variant="primary" icon="code-review" text="Help Header Override Example"](https://github.com/bashly-framework/bashly/tree/master/examples/help-header-override#readme)

### expose

[!badge Boolean / String]
[!badge variant="warning" text="Subcommands Only"]

Setting this to `true` or `always` on any command that has subcommands, will
show its subcommands in the help or usage text of the parent command.

- Set to `true` to show the subcommands only when the parent command is
  executed with `--help`.
- Set to `always` to show the subcommands also when the parent command is
  executed without any arguments.

You can use `expose` with the [`group`](#group) option, to show subcommands
in a logical, visual grouping.

[!button variant="primary" icon="code-review" text="Commands Expose Example"](https://github.com/bashly-framework/bashly/tree/master/examples/commands-expose#readme)


### extensible

[!badge Boolean / String]
[!badge variant="warning" text="Root Command Only"]

Specify that this command can be extended by external means.

[!ref](/advanced/extensible-scripts.md)


### filename

[!badge String]

The path (relative to `src`) to the partial source code file, in case you wish
to store your source files in a different path than the default one.

!!!success Tip
To instruct bashly to store *all* command files in sub-directories, see 
[Settings :icon-chevron-right: commands_dir](/usage/settings/#commands_dir)
!!!

[!button variant="primary" icon="code-review" text="Command Filenames Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-filenames#readme)


### filters

[!badge Array of Strings]

Add custom filter functions that will prevent the command from running unless 
certain conditions are met.

[!ref](/advanced/filters)


### function

[!badge String]

The base name of the internal functions bashly will use when generating the
script.

This is useful for scripts that contain several commands that otherwise evaluate
to the same internal function name.

Note that the name specified here is just used as a base name. Bashly will
generate several functions from it:

- `<cli name>_<base function name>_command`
- `<cli name>_<base function name>_usage`
- and possibly more

!!! Note
Under most circumstances you should avoid using this directive. It is provided
as a "last resort" mechanism to help in solving more complex scenarios.
!!!

[!button variant="primary" icon="code-review" text="Command Function Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-function#readme)



### private

[!badge Boolean]
[!badge variant="warning" text="Subcommands Only"]

Setting this to `true` on any command, will hide it from the command list.

!!!success Tip
To allow users to see private commands, see
[Settings :icon-chevron-right: private_reveal_key](/usage/settings/#private_reveal_key)
!!!

[!button variant="primary" icon="code-review" text="Private Command Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-private#readme)
`````

## File: src/configuration/dependency.md
`````markdown
---
icon: dot
order: 60
---

# Dependency

Specify a list of required external dependencies (commands). The script
execution will be halted with a friendly error unless all dependency commands
exist.

==- :icon-code-review: Show Me How
```yaml bashly.yml
# Array syntax
dependencies:
- docker
- curl

# Simple hash syntax, to provide additional (optional) help message
dependencies:
  docker: see https://docker.com for installation instructions
  git: "install by running: sudo apt install git"
  ruby:

# Explicit hash syntax, to provide additional help message and
# look for "one of" a given list of dependencies
dependencies:
  http_client:
    command: [curl, wget]
    help: Run 'sudo apt install curl' or 'sudo apt install wget'
```
===

This configuration option can be provided in one of three ways:

- A simple array, just listing the needed dependencies.
- A hash specifying an additional help message to show in case the dependency is
  not installed (for example, to provide installation instructions).
- A hash of hashes, providing a list of commands for a single dependency, and
  an optional help message. This is designed to provide an "or" functionality
  for a single dependency (for example: curl or wget).

When a command defines `dependencies`, it will also have the paths of the found
dependencies in an associative array named `deps`. Call the `inspect_args`
function from your command code to see this array.

[!button variant="primary" icon="code-review" text="Dependencies Example"](https://github.com/bashly-framework/bashly/tree/master/examples/dependencies#readme) [!button variant="primary" icon="code-review" text="Alternate Dependencies Example"](https://github.com/bashly-framework/bashly/tree/master/examples/dependencies-alt#readme)

## Basic Options

These options are valid when using the explicit hash syntax.

### command

[!badge Array of Strings]
[!badge variant="danger" text="Required"]

One or more commands that are required by your script. If more than one is
provided, the dependency will be considered as satisfied if any of the commands
exist.

For example, given this configuration:

```yaml bashly.yml
dependencies:
  http_client:
    command: [curl, wget]
    help: run 'sudo apt install curl' or 'sudo apt install wget'
```

the script will exit with the following error if both `curl` and `wget` are
not available:

```
$ ./myscript
missing dependency: http_client (curl/wget)
run 'sudo apt install curl' or 'sudo apt install wget'
```

### help

[!badge String]

An additional optional help message to show when the dependency is not met. 
This can be useful for providing installation instructions or a download URL.
`````

## File: src/configuration/environment-variable.md
`````markdown
---
icon: dot
order: 70
---

# Environment Variable

Specify environment variables (required or optional) used by your script.

==- :icon-code-review: Show Me How
```yaml bashly.yml
environment_variables:
  - name: config_path
    help: Location of the config file
    default: ~/config.ini
  - name: api_key
    help: Your API key
    required: true
  - name: app_env
    help: Application environment
    allowed: [dev, prod, test]
    default: dev
```
===

If an environment variable is defined as required (false by default), the
execution of the script will be halted with a friendly error if it is not set.

In addition, you can specify a default value for the environment variable, which
will be used in case the user has not defined it in their environment.

!!! Note
Most properties are optional, unless specified otherwise.
!!!


[!button variant="primary" icon="code-review" text="Environment Variables Example"](https://github.com/bashly-framework/bashly/tree/master/examples/environment-variables#readme)

## Basic Options

### name

[!badge String]
[!badge variant="danger" text="Required"]

The name of the variable. Use a lowercase name, it will be automatically
capitalized wherever needed.


### help

[!badge String]

The message to display when using `--help`. Can have multiple lines.



## Common Options

### default

[!badge String]

The value to use in case it is not provided by the user. Implies that this
environment variable is optional.

### private

[!badge Boolean]

Setting this to `true` on any environment variable, will hide it from the help
text.

!!!success Tip
To allow users to see private environment variables, see
[Settings :icon-chevron-right: private_reveal_key](/usage/settings/#private_reveal_key)
!!!

### required

[!badge Boolean]

Specify if this variable is required.

## Advanced Options

### allowed

[!badge Array of Strings]

Limit the allowed values to a specified whitelist. Can be used in conjunction
with [`default`](#default) or [`required`](#required).

### validate

[!badge String]

Apply a custom validation function.

[!ref](/advanced/validations)
`````

## File: src/configuration/flag.md
`````markdown
---
icon: dot
order: 80
---

# Flag

Specify flags (required or optional) used by your script.

==- :icon-code-review: Show Me How
```yaml bashly.yml
flags:
  - long: --ssh
    short: -s
    help: Clone using SSH.

  - long: --user
    short: -u
    arg: name
    help: Repository user name.
    required: true

  - long: --profile
    arg: name
    help: Profile name
    allowed: [production, stage, dev]
    default: dev

  - long: --verbose
    short: -v
    help: Verbosity level (up to -vvv)
    repeatable: true

  - long: --cache
    help: Enable cache
    conflicts: [--no-cache]

  - long: --no-cache
    help: Disable cache
    conflicts: [--cache]
```
===


The flag's value will be available to you as `${args[--output]}` in your bash
function (regardless of whether the user provided it with the long or short
form).

!!! Note
Bashly supports these additional flag formats as input:

- `-abc` same as `-a -b -c`
- `-a=arg` same as `-a arg`
- `--flag=arg` same as `--flag arg`
!!!

!!! Note
Most properties are optional, unless specified otherwise.
!!!

## Basic Options

### long

[!badge String]
[!badge variant="danger" text="Required (unless short is provided)"]

The long form of the flag, including the `--` prefix.


### short

[!badge String]
[!badge variant="danger" text="Required (unless long is provided)"]

The short form of the flag, including the `-` prefix.

!!! Note
If you define `short` only (without defining `long`), then the value
will be available to you in the `$args` associative array using the short name,
for example: `${args[-f]}`.
!!!

!!! Special handling for -v and -h
The `-v` and `-h` flags will be used as the short options for `--version` and `--help` respectively **only if you are not using them in any of your own flags**.
!!!


### help

[!badge String]

The text to display when using `--help`. Can have multiple lines.


### arg

[!badge String]

If the flag requires an argument, specify its name here.



## Common Options

### default

[!badge String / Array of Strings]

The value to use in case it is not provided by the user. Implies that this flag
is optional, and only makes sense when the flag has an argument.

When using [`repeatable`](#repeatable), you may provide an array here. It will
be provided to your script as a space delimited string (similar to how it is
provided when the user inputs values).

[!button variant="primary" icon="code-review" text="Default Values Example"](https://github.com/bashly-framework/bashly/tree/master/examples/default-values#readme)

### required

[!badge Boolean]

Specify if this flag is required.


## Advanced Options

### allowed

[!badge Array of Strings]

Limit the allowed arguments to a given whitelist. Can be used in conjunction
with [`default`](#default) or [`required`](#required).

Remember to set the [`arg`](#arg) name when using this option.

[!button variant="primary" icon="code-review" text="Whitelist Example"](https://github.com/bashly-framework/bashly/tree/master/examples/whitelist#readme)


### conflicts

[!badge Array of Strings]

Specify that this flag is mutually exclusive with one or more other flags.
The values of this array should be the long versions of the flags:  
`conflicts: [--other, --another]`

!!! Note
This option should be specified on both sides of the exclusivity.
!!!

[!button variant="primary" icon="code-review" text="Conflicts Example"](https://github.com/bashly-framework/bashly/tree/master/examples/conflicts#readme)


### completions

[!badge Array of Strings]

Specify an array of additional completion suggestions when used in conjunction
with `bashly add completions`.

Remember to set the [`arg`](#arg) name when using this option.

[!ref](/advanced/bash-completion.md)


### needs

[!badge Array of Strings]

Specify that this flag needs one or more other flags when executed.
The values of this array should be the long versions of the flags:  
`needs: [--other, --another]`

!!! Note
This option should be specified on both sides of the requirement.
!!!

[!button variant="primary" icon="code-review" text="Needy Flags Example"](https://github.com/bashly-framework/bashly/tree/master/examples/needs#readme)


### private

[!badge Boolean]

Setting this to `true` on any flag, will hide it from the help text.

!!!success Tip
To allow users to see private flags, see
[Settings :icon-chevron-right: private_reveal_key](/usage/settings/#private_reveal_key)
!!!

### repeatable

[!badge Boolean]

Specify that this flag can be provided multiple times.

When the flag does not have an argument, the user can provide it multiple times
in the form of `-v -v -v` or `-vvv`. In this case, the received value will be
the number of times it was entered.

When the flag has an argument, the user can provide it in the form of
`-d value1 -d "value 2"`. In this case, the received value will be formatted
as a quoted, space-delimited string which you will need to convert to array with
something like `eval "data=(${args[--data]})"`.

[!button variant="primary" icon="code-review" text="Repeatable Flag Example"](https://github.com/bashly-framework/bashly/tree/master/examples/repeatable-flag#readme)

### unique

[!badge Boolean]

Specify that the values for this flag must be unique. Non-unique values will be
ignored.

This option only applies to flags that have both `repeatable: true` and an `arg`
specified.

### validate

[!badge String]

Apply a custom validation function.

[!ref](/advanced/validations)
`````

## File: src/configuration/variable.md
`````markdown
---
icon: dot
order: 50
---

# Variable

This option allows you to define bash variables that will be accessible in your
script and its subcommands. While it's possible to define variables directly
within your bash script, this feature provides a structured alternative by
enabling you to centralize variable definitions in the YAML configuration file.

This approach helps to organize your variables separately from the main script
logic, improving readability and maintainability. It is important to note that
using this option is optional, and you can continue to define variables
directly in your bash script if preferred.

==- :icon-code-review: Show Me How
```yaml bashly.yml
variables:
  # Simple value
  - name: output_folder
    value: output

  # Array
  - name: download_sources
    value:
    - youtube
    - instagram

  # Associative array
  - name: zip_options
    value:
      pattern: "*.json"
      compression_level: fast
```
===

!!!success Tip 
Variables defined in the root command are available globally (in the
`initialize()` function), while those defined in subcommands are only accessible
within those specific commands.
!!!

[!button variant="primary" icon="code-review" text="Variables Example"](https://github.com/bashly-framework/bashly/tree/master/examples/variables#readme)

## Basic Options

### name

[!badge String]
[!badge variant="danger" text="Required"]

The name of the variable.

### value

[!badge Any Type]

The variable's value can be a simple type such as a string, number, or boolean,
or a one-level complex structure like an array or associative array (hash).
`````

## File: src/usage/getting-started.md
`````markdown
---
icon: rocket
order: 100
---

# Getting Started

Everything in bashly originates from a single configuration file, named `bashly.yml`.

This configuration file can be set up to generate two types of scripts:

1. Script with commands (for example, like `docker` or `git`).
2. Script without commands (for example, like `ls`)

This is detected automatically by the contents of the configuration: If it contains a `commands` definition, it will generate a script with commands.

In an empty directory, create a sample configuration file by running any of these commands:

```shell
$ bashly init

# or, to generate a simpler configuration:
$ bashly init --minimal
```

This will create a sample `src/bashly.yml` file. You can edit this file to specify which arguments, flags and commands you need in your bash script.

Then, generate an initial bash script and function placeholder scripts by running:

```shell
$ bashly generate
```

This will:

1. Create the bash executable script.
2. Create files for you to edit in the `src` folder.

Finally, edit the files in the `src` folder. Each of your script's commands get their own file. Once you edit, run `bashly generate` again to merge the content from your functions back into the script.
`````

## File: src/usage/settings.md
`````markdown
---
icon: tools
order: 80
---

# Settings

Some of bashly's commands can be tweaked through the use of environment
variables, or a settings file.

## Settings file

If you wish to load settings from a configuration file, you can generate an
initial settings file by running:

```shell
$ bashly add settings
```

which will create the default `settings.yml` file in the working directory.

Bashly will look for the settings file in one of these paths:

- A path set in the environment variable `BASHLY_SETTINGS_PATH`.
- A file named `bashly-settings.yml` in the working directory.
- A file named `settings.yml` in the working directory.

!!!success YAML Tips
- The words `yes` and `no` are equivalent to `true` and `false`
- To specify a `null` value, use `~`
!!!

[!button variant="primary" icon="code-review" text="Settings Example"](https://github.com/bashly-framework/bashly/tree/master/examples/settings#readme)

## Environment variables

All settings are optional (with their default values provided below), and
can also be set with an environment variable with the same name, capitalized
and prefixed by `BASHLY_` - for example: `BASHLY_SOURCE_DIR`

When setting environment variables, you can use:

- `0`, `false` or `no` to represent false
- `1`, `true` or `yes` to represent true

## Path Options

### `source_dir`

```yaml
# default
source_dir: src
```

Set the path containing the bashly source files.

### `config_path`

```yaml
# default
config_path: "%{source_dir}/bashly.yml"
```

Set the path to bashly.yml. You can use the special token `%{source_dir}` to
reference the value of the `source_dir` option.

### `target_dir`

```yaml
# default
target_dir: .
```

Set the path to use for creating the final bash script.

### `lib_dir`

```yaml
# default
lib_dir: lib
```

Set the path to use for common library files, relative to `source_dir`.

### `commands_dir`

```yaml
# default
commands_dir: ~

# example
commands_dir: commands
```

Set the path to use for command files, relative to `source_dir`.

- When set to `nil` (denoted by `~`), command files will be placed directly under `source_dir`.
- When set to any other string, command files will be placed under this
  directory, and each command will get its own sub-directory.

In case you plan on creating a large script with many commands, it is
recommended to enable this by setting it to something like
`commands_dir: commands`.

[!button variant="primary" icon="code-review" text="Command Paths Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-paths#readme)

### `partials_extension`

```yaml
# default
partials_extension: sh

# example
partials_extension: bash
```

Set the extension to use when reading/writing partial script snippets.

## Format Options

### `strict`

```yaml
# default
strict: false

# examples
strict: true
strict: ''
strict: set -o pipefail
```

Specify which bash options to apply on initialization.

- `strict: true` - Bash strict mode (`set -euo pipefail`)
- `strict: false` - Only exit on errors (`set -e`)
- `strict: ''` - Do not add any `set` directive
- `strict: <string>` - Add any other custom `set` directive, for example
   `strict: set -o pipefail`{style="white-space: nowrap;"}

### `tab_indent`

```yaml
# default
tab_indent: false
```

Specify the indentation style of the generated script.

- `tab_indent: false` - Indent with two spaces.
- `tab_indent: true` - Indent with Tab (every 2 leading spaces will be converted
   to a tab character).

### `formatter`

```yaml
# default
formatter: internal

# examples
formatter: external
formatter: none
formatter: shfmt
formatter: shfmt --minify
```

Choose a post-processor for the generated script:
- `formatter: internal`  
  Use Bashly's internal formatter. This formatter simply squashes any
  consecutive number of newlines to a single newline.
- `formatter: external`  
  Run the predefined external command `shfmt --case-indent --indent 2`. Depends on `shfmt` being available.
- `formatter: none`  
  Disable formatting entirely.
- `formatter: <string>`  
  Use a custom shell command to format the script. The command will receive the
  script via stdin and must output the result to stdout.

## Interface Options

### `compact_short_flags`

```yaml
# default
compact_short_flags: true
```

Specify how the generated script should treat flags in the form of `-abc`

- `compact_short_flags: true` - Expand `-abc` to `-a -b -c`.
- `compact_short_flags: false` - Do not expand `-abc` (consider this an invalid input).

### `conjoined_flag_args`

```yaml
# default
conjoined_flag_args: true
```

Specify how the generated script should treat flags in the form of `--flag=value`
or `-f=value`

- `conjoined_flag_args: true` - Expand `--flag=value` to `--flag value` and `-f=value` to `-f value`.
- `conjoined_flag_args: false` - Do not expand `--flag=value` or `-f=value` (consider this an invalid input).

### `show_examples_on_error`

```yaml
# default
show_examples_on_error: false
```

Specify if you want to show the
[command examples](/configuration/command/#examples) whenever the user fails to 
provide the required arguments.

[!button variant="primary" icon="code-review" text="Show Examples on Error Example"](https://github.com/bashly-framework/bashly/tree/master/examples/command-examples-on-error#readme)

### `private_reveal_key`

```yaml
# default
private_reveal_key: ~

# example
private_reveal_key: ADVANCED_FEATURES
```

When using private commands, flags, or environment variables, you may set 
this option to a name of an environment variable that, if set, will reveal
all the private elements in the usage texts, as if they were public.

[!button variant="primary" icon="code-review" text="Private Reveal Example"](https://github.com/bashly-framework/bashly/tree/master/examples/private-reveal#readme)

### `usage_colors`

```yaml
# default
usage_colors:
  caption: ~
  command: ~
  arg: ~
  flag: ~
  environment_variable: ~

# example
usage_colors:
  caption: bold
  command: green_underlined
  arg: blue
  flag: magenta
  environment_variable: cyan_bold
```

Enable color output for several aspects of the help message of the generated
script. Each of these options may be a name of a color function that exists in
your script, for example: `green` or `bold`.

You can run `bashly add colors` to add a standard colors library.

!!! Note
This option cannot be set using environment variables.
!!!

[!button variant="primary" icon="code-review" text="Usage Colors Example"](https://github.com/bashly-framework/bashly/tree/master/examples/colors-usage#readme)

## Feature Toggles

### `env`

```yaml
# default
env: development
```

Specify one of two script rendering environments:

- `env: development` - Generate a script suitable for development, which is usually slightly larger
   and contains additional development-specific features.
- `env: production` -  Generate a script suitable for distribution, which is usually smaller.

Use the `enable_*` options below to adjust settings for each environment.

!!! Note
It is recommended to leave this set to `development` in the settings file, and
use either the `BASHLY_ENV` environment variable or the
`bashly generate --env production` command when the slimmer production script is needed.
!!!


### `enable_header_comment`

```yaml
# default (allowed: always, never, development, production)
enable_header_comment: always
```

Specify if you wish to render the "do not modify" comment at the beginning of
the script.

### `enable_bash3_bouncer`

```yaml
# default (allowed: always, never, development, production)
enable_bash3_bouncer: always
```

Specify if you wish to render the piece of code that aborts the script execution
when bash version is < 4.2.

### `enable_view_markers`

```yaml
# default (allowed: always, never, development, production)
enable_view_markers: development
```

Specify if you want the rendered script to include view marker comments.

View markers provide the name of the internal bashly template (view) or the
path to the user's partial code files in the final script, to help locate
the source file for each piece of code.

### `enable_inspect_args`

```yaml
# default (allowed: always, never, development, production)
enable_inspect_args: development
```

Specify if you want the rendered script to include the `inspect_args()` function.

The `inspect_args()` function can help in reviewing the input for each command.

### `enable_deps_array`

```yaml
# default (allowed: always, never, development, production)
enable_deps_array: always
```

Specify if you want to populate the `$deps` bash array.

This is applicable only if your script uses the
[Dependency](/configuration/dependency) configuration option.

### `enable_env_var_names_array`

```yaml
# default (allowed: always, never, development, production)
enable_env_var_names_array: always
```

Specify if you want to populate the `$env_var_names` bash array.

This is applicable only if your script uses the
[Environment Variable](/configuration/environment-variable) configuration option.

### `enable_sourcing`

```yaml
# default (allowed: always, never, development, production)
enable_sourcing: development
```

Specify if you want the generated script to include a condition that checks if
the script was sourced and only execute it if it is not.

## Scripting Options

### `var_aliases`

```yaml
# default
var_aliases:
  args: ~
  other_args: ~
  deps: ~
  env_var_names: ~

# example
var_aliases:
  args: ARGS
  other_args: catch_all
  deps: dependencies
  env_var_names: ENV_VARS
```

Update one or more of these options in case you wish to change the name of the
public global array that bashly uses for storing data.

Note that this feature will not change the original name, but rather create
an alias using `declare -gn`.

!!! Note
This option cannot be set using environment variables.
!!!

### `function_names`

```yaml
# default
function_names:
  run: ~
  initialize: ~

# example
function_names:
  run: bashly_run
  initialize: bashly_initialize
```

Update one or more of these options in case you wish to change the name of the
equivalent internal bashly function.

This feature can be useful when you wish to reserve the function name `run` or
`initialize` for something else.

!!! Note
This option cannot be set using environment variables.
!!!
`````

## File: src/usage/testing-your-scripts.md
`````markdown
---
icon: codescan
order: 70
---

# Testing Your Scripts

## Static Code Analysis

The bash scripts generated by bashly are
[shellcheck](https://github.com/koalaman/shellcheck#readme) compliant, and
[shfmt](https://github.com/mvdan/sh) compliant.

This means that you can use these tools to ensure that any custom code you
use in your script, is also valid.

Note that when testing with `shfmt`, you should specify an indentation of 2
spaces, and case indentation rules:

```
$ shfmt --diff --case-indent --indent 2 yourscript
```

## Approval Testing

!!!success Tip
Run `bashly add test` to add a `test` folder to your project, with the 
Approvals.bash framework.
!!!

In cases where your scripts are more elaborate, or when you wish to ensure
your scripts behave as expected, you can use any bash testing framework to test
your scripts.

One such lightweight framework is
[Approvals.bash](https://github.com/dannyben/approvals.bash#readme), which lets
you test any command in your script and prompts you for interactive approval
of its output. Whenever the output changes, you will be prompted again to approve it.

A sample test script looks like this:

```bash
#!/usr/bin/env bash
source approvals.bash

approve "your-cli --help"
approve "your-cli command --arg"
# ... more tests
```
`````

## File: src/usage/writing-your-scripts.md
`````markdown
---
icon: code
order: 90
---

# Writing Your Scripts

The `bashly generate` command is performing the following actions:

1. Generates placeholder files in the `src` directory - one file for each of the
   defined commands in your `bashly.yml` file. These files are generated only once
   and are never overwritten.
2. Merges all these partial scripts into a single bash script, and saves it in
   the root directory of your project.

## Processing user input

In order to access the parsed arguments in any of your partial scripts, you may
simply access the `$args` associative array.

For example:

+++ Commands

```shell
# Generate a minimal configuration:
$ bashly init --minimal

# Generate the bash script:
$ bashly generate

# Run the script:
$ ./download hello --force
```

+++ Output

```shell
# this file is located in 'src/root_command.sh'
# you can edit it freely and regenerate (it will not be overwritten)
args:
- ${args[--force]} = 1
- ${args[source]} = hello
```

+++

You will notice that all the arguments of the associative array are printed on
screen. This is done by the `inspect_args` function that was inserted into the
generated partial script `src/root_command.sh`.

You can now access these variables by modifying `src/root_command.sh` like
this:

```bash src/root_command.sh
source_url=${args[source]}
force=${args[--force]}

if [[ $force ]]; then
  echo "downloading $source_url with --force"
else
  echo "downloading $source_url"
fi
```

After editing the file, run these commands:

+++ Commands

```shell
# Regenerate the script:
$ bashly generate   # or bashly g for short

# Test its new functionality:
$ ./download a --force
```

+++ Output

```shell
downloading a with --force
```

+++

## Adding common functions

In case you wish to add functions that can be used from multiple locations in
your code, you can place `*.sh` files inside the `src/lib` - these files will
be merged as is to the final bash script.

To get a starting point, you can run the convenience command:

```shell
$ bashly add lib
```

[!button variant="primary" icon="code-review" text="Custom Includes Example"](https://github.com/bashly-framework/bashly/tree/master/examples/custom-includes#readme)

## Hooks

### Initialization

Any code within the `src/initialize.sh` file will be called before anything else
in your generated bash script. 

!!!success Tip
If your script defines [Environment Variables](/configuration/environment-variable)
with [`default`](/configuration/environment-variable/#default) values, these
values will be available to you in the `initialize.sh` file.
!!!

### Before/after hooks

Any code within the `src/before.sh` file will be called before executing any
command, but after processing and validating the command line. Similarly, any
code within the `src/after.sh` file will be called after executing any command.

[!ref](/advanced/hooks)

## Custom header

In case you wish to replace the header in the generated script, simply put the new
content in `src/header.sh`.

!!! Note
Be sure to start your header with a shebang:
`#!/usr/bin/env bash`{style="white-space: nowrap;"}
!!!

!!!success Tip
If you just want to remove the header comment, you can adjust the
[`enable_header_comment`](/usage/settings/#enable_header_comment) setting instead.
!!!

## Hidden comments

Any comment in your source files that begins with two `#` symbols, will be 
removed from the final generated script. This is ideal for adding developer
notes that should not be visible to your end users.

```bash
## this comment will be hidden
# this one will be visible
```
`````

## File: src/demo.md
`````markdown
---
icon: terminal
layout: central
hidden: true
---

# Demo

[![Bashly Demo](assets/cast.gif)](assets/cast.gif)
`````

## File: src/examples.md
`````markdown
---
order: 85
icon: code-review
---

# Examples

The examples folder in the GitHub repository contains many detailed and
documented example configuration files, with their output.

[!button variant="primary" icon="code-review" text="View Examples on GitHub"](https://github.com/bashly-framework/bashly/tree/master/examples#readme)

All examples are listed below for convenience.

<!-- EXAMPLES INDEX -->
## Basic use

- [minimal](https://github.com/bashly-framework/bashly/tree/master/examples/minimal#readme) - the most basic "hello world" example
- [commands](https://github.com/bashly-framework/bashly/tree/master/examples/commands#readme) - a script with subcommands
- [commands-nested](https://github.com/bashly-framework/bashly/tree/master/examples/commands-nested#readme) - a script with nested subcommands

## Basic features

- [command-default](https://github.com/bashly-framework/bashly/tree/master/examples/command-default#readme) - configuring a default command
- [command-default-force](https://github.com/bashly-framework/bashly/tree/master/examples/command-default-force#readme) - configuring a default command that runs instead of showing the usage text
- [command-aliases](https://github.com/bashly-framework/bashly/tree/master/examples/command-aliases#readme) - allowing a command to be called with multiple names
- [command-examples](https://github.com/bashly-framework/bashly/tree/master/examples/command-examples#readme) - configuring command examples
- [dependencies](https://github.com/bashly-framework/bashly/tree/master/examples/dependencies#readme) - halting script execution unless certain dependencies are installed
- [dependencies-alt](https://github.com/bashly-framework/bashly/tree/master/examples/dependencies-alt#readme) - halting script execution unless one of the required dependencies is installed
- [environment-variables](https://github.com/bashly-framework/bashly/tree/master/examples/environment-variables#readme) - halting script execution unless certain environment variables are set
- [variables](https://github.com/bashly-framework/bashly/tree/master/examples/variables#readme) - defining bash variables
- [default-values](https://github.com/bashly-framework/bashly/tree/master/examples/default-values#readme) - arguments and flags with default values
- [minus-v](https://github.com/bashly-framework/bashly/tree/master/examples/minus-v#readme) - using `-v` and `-h` in your script
- [multiline](https://github.com/bashly-framework/bashly/tree/master/examples/multiline#readme) - help messages with multiple lines

## Advanced configuration features

- [catch-all](https://github.com/bashly-framework/bashly/tree/master/examples/catch-all#readme) - a command that can receive an arbitrary number of arguments
- [catch-all-advanced](https://github.com/bashly-framework/bashly/tree/master/examples/catch-all-advanced#readme) - another example for the `catch_all` option
- [catch-all-stdin](https://github.com/bashly-framework/bashly/tree/master/examples/catch-all-stdin#readme) - combining `catch_all` with `stdin` to read multiple files
- [extensible](https://github.com/bashly-framework/bashly/tree/master/examples/extensible#readme) - letting your script's users extend the script
- [extensible-delegate](https://github.com/bashly-framework/bashly/tree/master/examples/extensible-delegate#readme) - extending your script by delegating commands to an external executable
- [whitelist](https://github.com/bashly-framework/bashly/tree/master/examples/whitelist#readme) - arguments and flags with a predefined allowed list of values
- [repeatable-arg](https://github.com/bashly-framework/bashly/tree/master/examples/repeatable-arg#readme) - allowing arguments to be provided multiple times
- [repeatable-flag](https://github.com/bashly-framework/bashly/tree/master/examples/repeatable-flag#readme) - allowing flags to be provided multiple times
- [reusable-flags](https://github.com/bashly-framework/bashly/tree/master/examples/reusable-flags#readme) - reuse flag definition for multiple commands
- [conflicts](https://github.com/bashly-framework/bashly/tree/master/examples/conflicts#readme) - defining mutually exclusive flags
- [needs](https://github.com/bashly-framework/bashly/tree/master/examples/needs#readme) - defining flags that need other flags
- [command-private](https://github.com/bashly-framework/bashly/tree/master/examples/command-private#readme) - hiding commands from the command list
- [private-reveal](https://github.com/bashly-framework/bashly/tree/master/examples/private-reveal#readme) - allowing users to reveal private commands, flags or environment variables
- [stdin](https://github.com/bashly-framework/bashly/tree/master/examples/stdin#readme) - reading input from stdin
- [filters](https://github.com/bashly-framework/bashly/tree/master/examples/filters#readme) - preventing commands from running unless custom conditions are met
- [commands-expose](https://github.com/bashly-framework/bashly/tree/master/examples/commands-expose#readme) - showing subcommands in the parent's help
- [key-value-pairs](https://github.com/bashly-framework/bashly/tree/master/examples/key-value-pairs#readme) - parsing key=value arguments and flags
- [command-examples-on-error](https://github.com/bashly-framework/bashly/tree/master/examples/command-examples-on-error#readme) - showing examples on error
- [internal-run](https://github.com/bashly-framework/bashly/tree/master/examples/internal-run#readme) - calling other commands internally
- [command-line-manipulation](https://github.com/bashly-framework/bashly/tree/master/examples/command-line-manipulation#readme) - read or modify the raw command line

## Customization

- [colors-usage](https://github.com/bashly-framework/bashly/tree/master/examples/colors-usage#readme) - adding colors to the usage text
- [command-groups](https://github.com/bashly-framework/bashly/tree/master/examples/command-groups#readme) - grouping subcommands in logical sections
- [custom-strings](https://github.com/bashly-framework/bashly/tree/master/examples/custom-strings#readme) - configuring the script's error and usage texts
- [custom-includes](https://github.com/bashly-framework/bashly/tree/master/examples/custom-includes#readme) - adding and organizing your custom functions
- [custom-script-header](https://github.com/bashly-framework/bashly/tree/master/examples/custom-script-header#readme) - configuring a different script header
- [help-header-override](https://github.com/bashly-framework/bashly/tree/master/examples/help-header-override#readme) - replacing the header of the help message
- [footer](https://github.com/bashly-framework/bashly/tree/master/examples/footer#readme) - adding a footer to the help message
- [command-filenames](https://github.com/bashly-framework/bashly/tree/master/examples/command-filenames#readme) - overriding filenames for your source scripts
- [command-paths](https://github.com/bashly-framework/bashly/tree/master/examples/command-paths#readme) - configuring nested paths for your source scripts
- [command-function](https://github.com/bashly-framework/bashly/tree/master/examples/command-function#readme) - configuring custom internal function names
- [split-config](https://github.com/bashly-framework/bashly/tree/master/examples/split-config#readme) - splitting your `bashly.yml` into several smaller files

## Bashly library features

- [config](https://github.com/bashly-framework/bashly/tree/master/examples/config#readme) - using the config library for easy access to INI files
- [ini](https://github.com/bashly-framework/bashly/tree/master/examples/ini#readme) - using the ini library for direct, low level access to INI files
- [yaml](https://github.com/bashly-framework/bashly/tree/master/examples/yaml#readme) - using the YAML reading functions
- [colors](https://github.com/bashly-framework/bashly/tree/master/examples/colors#readme) - using the color print feature
- [completions](https://github.com/bashly-framework/bashly/tree/master/examples/completions#readme) - adding bash completion functionality
- [validations](https://github.com/bashly-framework/bashly/tree/master/examples/validations#readme) - adding validation functions for arguments, flags or environment variables
- [hooks](https://github.com/bashly-framework/bashly/tree/master/examples/hooks#readme) - adding before/after hooks
- [stacktrace](https://github.com/bashly-framework/bashly/tree/master/examples/stacktrace#readme) - adding stacktrace on error

## Real-world-like examples

- [docker-like](https://github.com/bashly-framework/bashly/tree/master/examples/docker-like#readme) - a sample script with deep commands (like `docker container run`)
- [git-like](https://github.com/bashly-framework/bashly/tree/master/examples/git-like#readme) - a sample script with subcommands similar to git

## Documentation generation

- [render-mandoc](https://github.com/bashly-framework/bashly/tree/master/examples/render-mandoc#readme) - auto-generate man pages for your script
- [render-markdown](https://github.com/bashly-framework/bashly/tree/master/examples/render-markdown#readme) - auto-generate markdown documentation for your script

## Other examples

- [settings](https://github.com/bashly-framework/bashly/tree/master/examples/settings#readme) - using the `settings.yml` file to adjust bashly's behavior
- [help-command](https://github.com/bashly-framework/bashly/tree/master/examples/help-command#readme) - adding a help command to your script

<!-- EXAMPLES INDEX -->


## Real world examples

If you're interested in real-world examples developed by the bashly community,
check out the [Made with Bashly](https://github.com/bashly-framework/bashly/wiki/Made-with-Bashly)
wiki page.
`````

## File: src/index.md
`````markdown
---
icon: home
order: 100
label: Welcome
meta:
  title: "Bashly - Bash Command Line Framework"
---

# Welcome to Bashly

Bashly is a command line application (written in Ruby) that lets you
generate feature-rich bash command line tools.

Bashly lets you focus on your specific code, without worrying
about command line argument parsing, usage texts, error messages and other
functions that are usually handled by a framework in any other programming
language.

[![Bashly Demo](/assets/cast.gif)](/demo/)

## How it works

1. You provide a YAML configuration file, describing commands, subcommands,
   arguments, and flags. Running `bashly init` creates an initial sample YAML
   file for you ([example](https://github.com/bashly-framework/bashly/tree/master/examples/minimal#bashlyyml)).
2. Bashly then automatically generates a bash script (when you run
   `bashly generate`) that can parse and validate user input, provide help
   messages, and run your code for each command.
3. Your code for each command is kept in a separate file, and can be merged
   again if you change it ([example](https://github.com/bashly-framework/bashly/blob/master/examples/minimal/src/root_command.sh)).

## Features

Bashly is responsible for:

- Generating a **single, standalone bash script**.
- Generating a **human readable, shellcheck-compliant and shfmt-compliant script**.
- Generating **usage texts** and help screens, showing your tool's arguments, flags and commands (works for subcommands also).
- Parsing the user's command line and extracting:
  - Optional or required **positional arguments**.
  - Optional or required **option flags** (with or without flag arguments).
  - **Commands** (and subcommands).
  - Standard flags (like **--help** and **--version**).
- Preventing your script from running unless the command line is valid.
- Providing you with a place to input your code for each of the functions your tool performs, and merging it back to the final script.
- Providing you with additional (optional) framework-style, standard library functions:
  - **Color output**.
  - **Config file management** (INI format).
  - **YAML parsing**.
  - **Bash completions**.
  - *and more*.
- Auto-generating **markdown and man page documentation** for your script.
`````

## File: src/installation.md
`````markdown
---
icon: terminal
order: 99
---

# Installation

Install bashly using one of these methods.

+++ Ruby Gem

Bashly requires Ruby 3.2 or higher (`ruby -v`).

```shell
gem install bashly
```

[!ref](/installing-ruby)

+++ Docker

If you have docker installed, you can create an alias that will run the docker image:

```shell
alias bashly='docker run --rm -it --user $(id -u):$(id -g) --volume "$PWD:/app" dannyben/bashly'
```

The bashly docker image can also be installed using Whalebrew:

```shell
whalebrew install dannyben/bashly
```

+++

## Bash Completions

To enable bash completions for the `bashly` executable itself run:

```shell
bashly completions --install
```

You might need to install the `bash-completion` package for your operating
system if it is not already installed. For example:

```shell
brew install bash-completion
# or
sudo apt install bash-completion
```

!!!success Tip
To generate bash completions for your own scripts, see  
[Advanced Features :icon-chevron-right: Bash Completion](/advanced/bash-completion/)
!!!

## Prerequisites

The bash scripts generated by bashly can run in any shell, but require that
**bash 4.2 or higher** is installed.

Mac users can upgrade bash by running:

```
brew install bash
```
`````

## File: src/installing-ruby.md
`````markdown
---
order: 10
icon: ruby
---

# Installing Ruby

The installation instructions provided below aim to be the fastest and simplest
way to install Ruby, with the ability to install gems that build native
extensions.

The general instructions are:

1. **Install build tools / development tools**  
   Each operating system's package manager has its own "meta package" that 
   installs some compilers and other packages needed for building other
   packages.
2. **Install libyaml**  
   Many Ruby gems rely on this library.
3. **Ensure the gem bin path is in your `$PATH`**  
   Some installation methods do not update the `$PATH` properly. You will need
   to alter your `$PATH` so that it includes the path to the location of gem
   executable files.

## `brew` - macOS

```bash
$ brew install ruby
$ gem install bashly
```

## `apt` - Ubuntu / Debian

```bash
$ sudo apt -y update
$ sudo apt -y install build-essential libyaml-dev ruby-dev
$ sudo gem install bashly
```

## `pacman` - Arch Linux

```bash
$ sudo pacman -Suy
$ sudo pacman -S base-devel ruby

# add gem bin dir to path (put this in your initialization script if needed)
$ export PATH="$PATH:$(gem env path | sed 's#[^:]\+#&/bin#g')"

$ gem install bashly
```

## `dnf` - Fedora / CentOS / Red Hat

```bash
$ sudo dnf -y update
$ sudo dnf -y install @development-tools libyaml-devel ruby-devel
$ gem install bashly
```
`````
