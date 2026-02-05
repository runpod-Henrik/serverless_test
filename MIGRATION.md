# Migration Guide

This guide documents the migration of the flaky test detector to https://github.com/runpod/testflake

## Project Name

**`testflake`** - Short, memorable, clearly indicates flaky test detection.

## Migration Steps

### Phase 1: Prepare Current Repository

#### 1. Clean Up Files (see CLEANUP.md)

```bash
# Run cleanup script
bash scripts/cleanup_for_migration.sh

# Review what will be included
git status
```

#### 2. Create Migration Branch

```bash
git checkout -b migration-prep
```

#### 3. Update All References

**Files to update with new org/repo name:**

```bash
# Update repository URLs in:
- README.md (all GitHub links)
- docs/GETTING_STARTED.md (clone URLs)
- docs/README.md (external links)
- docs/CICD_INTEGRATION.md (workflow examples)
- setup.sh (default repo URL)
- test_input.json (repo field)
- .github/workflows/*.yml (comments/docs)
```

**Search and replace:**
```bash
# All references have already been updated to runpod/testflake
# This step is complete!
grep -r "runpod/testflake" .  # Verify new references
```

#### 4. Update Package/Module Names

If renaming (e.g., to flaky-shield):

```bash
# Update Python module references if needed
# Most files use direct imports, so minimal changes needed

# Update any package.json, setup.py, or pyproject.toml
# (currently not applicable, but check if added)
```

### Phase 2: Create New Repository

#### 1. Create Repository on GitHub

1. Go to RunPod organization: `https://github.com/organizations/runpod/repositories/new`
2. Name: `testflake`
3. Description: "Automated flaky test detection with parallel execution and CI integration"
4. **Do NOT** initialize with README (we'll push existing)
5. Set visibility (Public recommended)
6. Create repository at: `https://github.com/runpod/testflake`

#### 2. Update Local Git Remote

```bash
# Add new remote
git remote add new-origin git@github.com:runpod/testflake.git

# Or update existing origin
git remote set-url origin git@github.com:runpod/testflake.git

# Verify
git remote -v
```

#### 3. Push to New Repository

```bash
# Push main branch
git push -u new-origin main

# Push all branches (if any)
git push -u new-origin --all

# Push tags (if any)
git push -u new-origin --tags
```

### Phase 3: Configure New Repository

#### 1. Repository Settings

**General:**
- ✅ Enable Issues
- ✅ Enable Wiki (optional)
- ✅ Enable Discussions (optional)
- ✅ Allow squash merging
- ✅ Automatically delete head branches

**Branches:**
- Set `main` as default branch
- Add branch protection rules:
  - ✅ Require pull request before merging
  - ✅ Require status checks to pass
  - ✅ Require branches to be up to date

**Actions:**
- ✅ Allow all actions
- ✅ Allow GitHub Actions to create PRs

#### 2. Add Repository Secrets (if using RunPod)

Go to Settings → Secrets and variables → Actions:

- `RUNPOD_API_KEY` - Your RunPod API key
- `RUNPOD_ENDPOINT_ID` - Deployed endpoint ID
- `ANTHROPIC_API_KEY` - (Optional) For AI workflow suggestions

#### 3. Add Topics/Tags

Suggested topics:
- `testing`
- `flaky-tests`
- `ci-cd`
- `github-actions`
- `test-automation`
- `python`
- `go`
- `typescript`
- `javascript`

#### 4. Create Initial Release

```bash
# Tag current state
git tag -a v1.0.0 -m "Initial public release"
git push new-origin v1.0.0

# Create release on GitHub
# Go to: Releases → Draft a new release
# Tag: v1.0.0
# Title: "v1.0.0 - Initial Release"
# Description: See CHANGELOG.md
```

### Phase 4: Update Documentation

#### 1. Create CHANGELOG.md

```markdown
# Changelog

## [1.0.0] - 2026-02-05

### Initial Release

- Automated flaky test detection
- Multi-language support (Python, Go, TypeScript, JavaScript)
- GitHub Actions auto-trigger
- Interactive dashboard
- Comprehensive documentation
- 96 tests, 91% coverage
```

#### 2. Update README.md

Replace setup URL:
```markdown
```bash
# Old
bash <(curl -s https://raw.githubusercontent.com/runpod/testflake/main/setup.sh)

# New
bash <(curl -s https://raw.githubusercontent.com/NEW_ORG/flaky-shield/main/setup.sh)
```
```

#### 3. Add Contributing Guide

Create `CONTRIBUTING.md`:
```markdown
# Contributing to Flaky Shield

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `./scripts/run_all_checks.sh`
5. Submit a pull request

See [Quality Checks](docs/QUALITY_CHECKS.md) for standards.
```

#### 4. Add License

Choose and add LICENSE file (MIT recommended):
```bash
# Copy from GitHub's license templates
# https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
```

### Phase 5: Announcement & Cleanup

#### 1. Update Old Repository

Add deprecation notice to old README:

```markdown
# ⚠️ MOVED

This repository has moved to:
**https://github.com/NEW_ORG/flaky-shield**

Please update your bookmarks and references.
```

Archive the old repository:
- Settings → General → Archive this repository

#### 2. Update Links

Update any external references:
- Documentation sites
- Blog posts
- Social media
- Package registries (if applicable)

#### 3. Announce

- Create announcement issue
- Post on relevant forums/communities
- Update any related projects

## Migration Checklist

### Pre-Migration

- [ ] Run cleanup script
- [ ] Review and consolidate documentation
- [ ] Update all repository references
- [ ] Test locally after changes
- [ ] Create migration branch

### Repository Setup

- [ ] Create new repository
- [ ] Update git remotes
- [ ] Push all branches and tags
- [ ] Configure repository settings
- [ ] Add secrets (if needed)
- [ ] Add topics/tags
- [ ] Create initial release

### Documentation

- [ ] Create CHANGELOG.md
- [ ] Update README.md with new URLs
- [ ] Add CONTRIBUTING.md
- [ ] Add LICENSE
- [ ] Update all doc cross-references
- [ ] Test all documentation links

### Post-Migration

- [ ] Archive old repository
- [ ] Update external references
- [ ] Test setup.sh from new location
- [ ] Verify CI/CD works
- [ ] Announce migration

### Verification

- [ ] Clone fresh copy and test setup
- [ ] Run `./scripts/run_all_checks.sh`
- [ ] Test `python3 local_test.py`
- [ ] Verify GitHub Actions workflows
- [ ] Check all documentation links

## Migration Status

✅ **All references updated to runpod/testflake**

The codebase has been prepared for migration:
- All URLs updated from `runpod-Henrik/serverless_test` to `runpod/testflake`
- All directory references updated to `testflake`
- Documentation consolidated and cross-references fixed

Ready to push to the new repository!

## Troubleshooting

### Setup script fails with 404

Update the raw GitHub URL in setup.sh or in documentation curl commands.

### Old URLs in documentation

Search for any remaining old references:
```bash
grep -r "runpod-Henrik" .  # Should find nothing
grep -r "runpod/testflake" .  # Verify new references
```

### CI workflows fail

Check repository secrets are set correctly in new repo.

### Links broken after migration

Use GitHub's "Search this repository" to find old URLs:
```
runpod/testflake
```

## Need Help?

- Open an issue in the new repository
- Check documentation at `docs/README.md`
- Review example configurations in `examples/`

---

**Good luck with your migration!** 🚀
