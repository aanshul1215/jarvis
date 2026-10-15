# Owner setup requirements — proposed, no credentials requested here

1. Choose a local `JARVIS_HOME` **outside the cloned repository**, with restricted access, adequate disk and an encrypted backup location. A1 will provide a path validation/restore tool; it does not exist yet.
2. Confirm development OS, RAM, disk, clock sync, internet and sleep behavior. The 8 GB Windows laptop is a design constraint, not a benchmarked runtime.
3. Review [owner decisions](OWNER_DECISIONS_REQUIRED.md) and [read-only probes](PROBE_REGISTER.md). Keep unknown provider permissions OPEN.
4. If paper access is approved later, enter paper-only credentials into the OS credential store using the future local setup tool. **Never send keys in chat, screenshots, Git or sample files.** No live credentials are needed for A0–A4.
5. Start in OFF or mock/OBSERVE, then SHADOW and PAPER only after their gates. LIVE is disabled in V1 development. Verify current broker positions and orders before each restart resumes any order path.
6. Review CSV reports as copies in Excel. Do not edit journal files or assume a report edit changes trading state.

No installation command or runnable trading service exists in this documentation branch. The first actionable task is [A0-01](../../EXECUTION.md).
