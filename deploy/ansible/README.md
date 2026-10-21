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

## Workflows

Workflows are declared in `cloudgene_workflows` in `group_vars/all/vars.yml`. For each entry the
`workflows` role downloads the release zip to `/opt/cloudgene-workflows/<id>/`, links the app's
`cloudgene.yml` to a file in the `qcif/daff-cloudgene` clone (`/opt/daff-cloudgene`), and runs
`manage.py ensure_workflow` to register it with the given access, `profile`, `work_dir` and
`trust_output`.

- **Add:** append an entry (see the Taxodactyl example) and re-run the playbook.
- **Upgrade/replace:** change `archive_url`, `archive_root` and `cloudgene_yml` to the new
  version's values (use a new `id` if both versions should stay installed).
- **Remove:** set `state: absent`, run the playbook (unregisters it and deletes the files), then
  delete the entry.
- Per-app `nextflow.env` / `nextflow.config` (credentials) are not managed here; set them in
  Admin > Workflows.
- The `ensure_workflow` / `uninstall_workflow` commands are in this repo, so the server needs a
  code version that has them (`cloudgene_version`).

## On the server

```
sudo -u cloudgene cloudgene-manage <command>      # manage.py with the production env
systemctl status cloudgene-web cloudgene-worker cloudgene-cleanup.timer
journalctl -u cloudgene-worker -f
curl https://<domain>/api/health
```

Backups (`pg_dump` and `/var/lib/cloudgene`) are not automated; see DEPLOYMENT.md section 6.
