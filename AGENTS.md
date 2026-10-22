# Cloudgene4 development

Please refer to ./spec/ for application specifications. Ensure that any changes
you make respect the spec. You should start every task by reading the 
./spec/constitution.md, and any spec that you decide is relevant to your
understanding.

If you already have a task brief, chances are that you already have the context
you need, but you should always read the constitution.

Significant development work should not be undertaken without a task brief -
those live in ./tasks/. Task completion can be marked by moving the brief to
./tasks/completed/. A task can be shelved (for deferring execution) by moving
to ./tasks/shelved/, or archived by moving to ./tasks/shelved/archived/.

## Virtual environments

The project should create ./venv/ for working with Python code.

A CLAUDE_VENV may be accessible at ~/.local/envs/claude. If not, create one in
.claude/venv/.

For running Ansible, you should first see if ~/.local/envs/ansible is available,
otherwise fall back to the project venv or CLAUDE_VENV.
