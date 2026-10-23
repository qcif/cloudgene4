# Deploy with Ansible

In main (not in a worktree):

```sh
git checkout main
cd deploy/ansible
. ~/.local/envs/ansible/bin/activate
ansible-playbook site.yml
```
