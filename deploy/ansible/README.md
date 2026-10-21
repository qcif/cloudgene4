# Ansible deployment

Deploys Cloudgene to a single Ubuntu 26.04 host: nginx (Let's Encrypt TLS) -> gunicorn
(`cloudgene-web`) + `run_worker` (`cloudgene-worker`) + a daily cleanup timer, backed by
PostgreSQL, with Java 21 and Nextflow for running workflows. It automates
[`docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md) and installs the repo's own
`deploy/systemd/*` units.

## Before the first run

1. Point a DNS A record for your domain at the VM, and open ports 80/443 in the cloud
   security group.
2. Edit `group_vars/all/vars.yml`: at least `cloudgene_domain` and
   `cloudgene_letsencrypt_email` (also `cloudgene_repo` / `cloudgene_version` if needed).
3. Create the secrets:
   ```
   cp group_vars/all/vault.yml.example group_vars/all/vault.yml
   $EDITOR group_vars/all/vault.yml
   ansible-vault encrypt group_vars/all/vault.yml
   ```
4. `ansible-galaxy collection install -r requirements.yml`
5. The inventory uses the `cloudgene4` SSH alias from `~/.ssh/config`.

## Deploy / upgrade

```
cd deploy/ansible
ansible-playbook site.yml --ask-vault-pass
```

Re-running pulls the configured branch, reinstalls requirements, rebuilds the frontend if the
code changed, migrates, and restarts the services. Set `cloudgene_tls_enabled: false` to serve
plain HTTP (e.g. before DNS is ready); flip it on and re-run to obtain the certificate.

## On the server

```
sudo -u cloudgene cloudgene-manage <command>      # manage.py with the production env
systemctl status cloudgene-web cloudgene-worker cloudgene-cleanup.timer
journalctl -u cloudgene-worker -f
curl https://<domain>/api/health
```

Backups (`pg_dump` and `/var/lib/cloudgene`) are not automated; see DEPLOYMENT.md section 6.
