# AI coding assistant skills

This repo ships an agent skill, [`skills/hlthstack-api`](../skills/hlthstack-api/SKILL.md),
that teaches AI coding assistants how the hlthstack API works: the base URLs and auth, the
booking, consultation, ePharmacy, wallet and pre-registration flows, webhook verification,
and the field rules that commonly trip people up. With it installed, the assistant reads
the OpenAPI spec instead of guessing endpoints, and asks before it creates, reschedules or
cancels anything.

The skill follows the open [Agent Skills](https://agentskills.io/) format (a folder with a
`SKILL.md`), so the same folder works in Claude Code, OpenAI Codex and ChatGPT. The folder is
self-contained: `references/` holds copies of the OpenAPI spec and the API guides, so the
assistant reads them locally however the skill was installed, without fetching anything. The
repo is also a plugin marketplace for both Claude (`.claude-plugin/`) and OpenAI
(`.agents/plugins/marketplace.json` and `.codex-plugin/`), which keeps the skill up to date
with this repo.

| Tool | Quickest install | Run it |
|---|---|---|
| Claude Code | `claude plugin marketplace add hlthstack/integration-guide` then `claude plugin install hlthstack@hlthstack` | Ask about hlthstack, or type `/hlthstack:hlthstack-api` |
| Codex | `codex plugin marketplace add hlthstack/integration-guide` then `codex plugin add hlthstack@hlthstack` | Ask about hlthstack, or type `$` and pick `hlthstack-api` |
| ChatGPT (Business, Enterprise, Edu) | Admin imports `https://github.com/hlthstack/integration-guide` as a plugin marketplace, or upload the skill | Ask about hlthstack, or mention `@hlthstack` |

How the three assistants compare:

| | Claude Code | Codex | ChatGPT |
|---|---|---|---|
| Plugin install | [Option 1](#option-1-install-as-a-plugin-recommended): each developer runs two commands | [Option 1](#option-1-install-as-a-plugin-recommended-1): each developer runs two commands | [Option 1](#option-1-import-the-plugin-marketplace-workspace-admins): a workspace admin imports the marketplace |
| Other ways to install | Copy the skill folder | Codex's skill installer, or copy the skill folder | Upload the skill as a zip |
| Plugin updates | `claude plugin marketplace update` and `claude plugin update`, then restart | `codex plugin marketplace upgrade` | Synced daily |
| Pick the skill explicitly | `/hlthstack:hlthstack-api` (plugin) or `/hlthstack-api` (folder) | `$hlthstack-api`, or `/skills` | `@hlthstack` (plugin), or **+** in the composer |
| Calls the API | Asks before running commands that call it | Asks before running commands that call it | No: run the code it writes yourself |

> [!CAUTION]
> Never paste API credentials into the assistant's chat. Keep them in environment variables
> or your secret manager; see [credentials and safety](#credentials-and-safety).

## Claude Code

1. Install the skill: as a plugin ([option 1](#option-1-install-as-a-plugin-recommended)) or
   by copying the folder ([option 2](#option-2-copy-the-skill-folder)).
2. Start Claude Code in your project and ask about hlthstack
   ([run it](#run-it-in-claude-code)).

### Option 1: install as a plugin (recommended)

The repo is a Claude Code plugin marketplace. Installing the plugin keeps the skill
up to date with this repo.

1. Add the marketplace and install the plugin:

   ```bash
   claude plugin marketplace add hlthstack/integration-guide
   claude plugin install hlthstack@hlthstack
   ```

   The same commands work inside a Claude Code session:

   ```text
   /plugin marketplace add hlthstack/integration-guide
   /plugin install hlthstack@hlthstack
   ```

2. Check it's installed:

   ```bash
   claude plugin details hlthstack@hlthstack
   ```

Each developer runs these once. To give your whole team the skill without any install
step, use option 2 at project level and commit the folder.

Update to the latest version, then restart Claude Code:

```bash
claude plugin marketplace update hlthstack
claude plugin update hlthstack@hlthstack
```

Remove it:

```bash
claude plugin uninstall hlthstack@hlthstack
claude plugin marketplace remove hlthstack
```

### Option 2: copy the skill folder

For all your projects (personal skill):

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p ~/.claude/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api ~/.claude/skills/
```

For one project only, run this from the project's root and commit the folder so your team
gets it too:

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p .claude/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api .claude/skills/
```

To update, delete the copied `hlthstack-api` folder and copy it again. Claude Code picks up
the change without a restart. If the `skills` folder didn't exist when the session
started, run `/reload-skills`.

### Run it in Claude Code

Start Claude Code in your project and ask about hlthstack. Claude loads the skill on its
own when the request matches:

```bash
claude
```

```text
> Write a Node.js function that books a health checkup on hlthstack staging for one member
```

To load it explicitly, type the skill's slash command, followed by your request:

- installed as a plugin: `/hlthstack:hlthstack-api`
- copied into a skills folder: `/hlthstack-api`

```text
> /hlthstack:hlthstack-api add a webhook endpoint in our Express app that verifies the Signature header
```

Without the interactive UI (for example in a script):

```bash
claude -p "Using the hlthstack API, which header does pre-registration use for its token?"
```

## Codex

1. Install the skill: as a plugin
   ([option 1](#option-1-install-as-a-plugin-recommended-1)), with Codex's skill installer
   ([option 2](#option-2-install-with-codexs-skill-installer)) or by copying the folder
   ([option 3](#option-3-copy-the-skill-folder)).
2. Start Codex in your project and ask about hlthstack ([run it](#run-it-in-codex)).

### Option 1: install as a plugin (recommended)

The repo is a Codex plugin marketplace. Installing the plugin keeps the skill up to date
with this repo.

1. Add the marketplace and install the plugin:

   ```bash
   codex plugin marketplace add hlthstack/integration-guide
   codex plugin add hlthstack@hlthstack
   ```

2. Check it's available:

   ```bash
   codex plugin list
   ```

Update to the latest version of the repo:

```bash
codex plugin marketplace upgrade hlthstack
```

Remove it:

```bash
codex plugin remove hlthstack@hlthstack
codex plugin marketplace remove hlthstack
```

Codex also reads plain skill folders from `.agents/skills` in your repository (from the
folder you start Codex in up to the repository root) and from `~/.agents/skills` for your
user. Options 2 and 3 install the skill on its own that way.

### Option 2: install with Codex's skill installer

1. Start Codex:

   ```bash
   codex
   ```

2. Ask its built-in installer to fetch the skill from GitHub:

   ```text
   > $skill-installer install https://github.com/hlthstack/integration-guide/tree/main/skills/hlthstack-api
   ```

3. Codex usually picks up a new skill on its own; if `$hlthstack-api` doesn't show up,
   restart Codex.

The installer puts the skill in `~/.codex/skills/hlthstack-api` (under `$CODEX_HOME` if you
set it). To update, delete that folder and run the install again; to remove the skill,
delete the folder:

```bash
rm -rf ~/.codex/skills/hlthstack-api
```

### Option 3: copy the skill folder

For all your projects:

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p ~/.agents/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api ~/.agents/skills/
```

For one project only, run this from the repository root and commit the folder:

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p .agents/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api .agents/skills/
```

To update, delete the copied `hlthstack-api` folder and copy it again.

### Run it in Codex

Start Codex in your project and ask about hlthstack; Codex uses the skill when the request
matches its description. To pick it explicitly, type `$` and choose `hlthstack-api`, run
`/skills`, or mention it in the prompt (installed as a skill folder):

```text
> $hlthstack-api write a Python script that pre-registers members from members.csv on staging
```

Without the interactive UI:

```bash
codex exec '$hlthstack-api Which header does hlthstack pre-registration use for its token?'
```

Use single quotes so your shell doesn't expand `$hlthstack-api`.

## ChatGPT

1. Make the skill available: a workspace admin imports the plugin marketplace
   ([option 1](#option-1-import-the-plugin-marketplace-workspace-admins)), or you upload the
   skill ([option 2](#option-2-upload-the-skill)).
2. Ask about hlthstack in any chat ([run it](#run-it-in-chatgpt)).

ChatGPT uses the same skills and plugins as Codex. Skills and plugin uploads are available
on ChatGPT Business, Enterprise, Healthcare and Edu, subject to your workspace settings.

### Option 1: import the plugin marketplace (workspace admins)

1. In ChatGPT, open **Admin console**, choose your workspace and open **Plugins**.
2. Select **Add** -> **Import marketplace**.
3. **Source**: `https://github.com/hlthstack/integration-guide`. Leave **Path** and
   **Branch** empty.
4. Select **Import marketplace**, authorize GitHub access if asked, then set the `hlthstack`
   plugin's installation policy for your members.

ChatGPT syncs the marketplace daily, so members get updates to the skill automatically.

### Option 2: upload the skill

1. Download the skill: on GitHub, open
   [`skills/hlthstack-api`](https://github.com/hlthstack/integration-guide/tree/main/skills/hlthstack-api),
   or clone the repo, and zip the `hlthstack-api` folder.
2. In ChatGPT, select **Plugins** in the sidebar, open the **Skills** tab, then **Create** ->
   **Upload from your computer**, and choose the zip.
3. ChatGPT scans the skill; it's usually available as soon as the scan finishes. Share it
   with your workspace from the skill's **•••** menu if you want.

### Run it in ChatGPT

Ask about hlthstack in any chat; ChatGPT uses the skill when it's relevant. To pick it
explicitly, mention `@hlthstack` (plugin) or select the skill from **+** in the composer.

> [!NOTE]
> ChatGPT can explain the API and write integration code with the skill, but it doesn't call
> the hlthstack API for you. Run the code it writes from your own environment.

### Custom GPTs

> [!WARNING]
> Earlier versions of this repo described a custom GPT with an action for the hlthstack API.
> OpenAI is retiring custom GPTs on 11 December 2026 (later for some Enterprise workspaces),
> and a GPT's custom actions don't carry over when it's migrated to a plugin. If you built
> that GPT, replace it with the plugin or skill above.

## Credentials and safety

> [!CAUTION]
> Keep API credentials in environment variables (for example `HLTHSTACK_USERNAME`, `HLTHSTACK_PASSWORD`) or
> your secret manager. Don't paste them into the chat.

- The skill tells the assistant to read credentials from the environment and never print or
  hard-code them.
- The skill uses staging unless you ask for production, and asks before creating,
  rescheduling or cancelling bookings or orders, or changing pre-registered members.
- Both tools ask before running commands that call the API.

> [!WARNING]
> Review what the assistant runs, especially against production.

## Example prompts

Prompts that work well with the skill:

- "Generate a typed client for the hlthstack consultation endpoints we use."
- "Our `createAppointment` call returns 422; here's the request and response. What's wrong?"
- "Add a webhook handler that verifies the hlthstack `Signature` header and updates our
  appointment status."
- "Write a script that pre-registers the members in `members.csv` on staging and polls until
  the request completes."
- "Move our hlthstack calls from plain `fetch` to the `hlthstack` JS SDK."

## Maintaining the skill

`skills/hlthstack-api/references/` is generated from `openapi/` and `docs/`.

1. After changing either, regenerate it and commit the result; CI fails if the copies are out
   of date:

   ```bash
   python3 scripts/sync_skill_references.py
   ```

2. When the skill or its references change, bump `version` in both
   `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, so plugin installs pick up the update.
