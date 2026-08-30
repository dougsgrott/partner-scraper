"""MDX → Markdown. See PLAN.md §7.1 and docs/validation-plan.md.

Every case below is taken from a real Anthropic docs page. The components are inert as
published — `<Card href=…>` hides 562 links from any Markdown parser — and the human
review pass reported exactly that, as "the Next steps links are missing".
"""

from __future__ import annotations

from scraper.extract import mdx

CARDS = """## Next steps

<CardGroup cols={3}>
  <Card title="CLI authentication options" icon="lock" href="https://platform.claude.com/docs/en/cli-sdks-libraries/cli/authentication">
    API keys, headless hosts, multiple workspaces, and named profiles
  </Card>

  <Card title="Using the CLI" icon="terminal" href="https://platform.claude.com/docs/en/cli-sdks-libraries/cli/using">
    Command structure, output formats, GJSON transforms, and request bodies
  </Card>
</CardGroup>
"""


def test_cards_become_markdown_links():
    """REGRESSION: the links were present but unreachable — no parser sees `href=`."""
    out = mdx.to_markdown(CARDS)
    assert ("- [CLI authentication options]"
            "(https://platform.claude.com/docs/en/cli-sdks-libraries/cli/authentication)"
            " — API keys, headless hosts, multiple workspaces, and named profiles") in out
    assert "<Card" not in out and "<CardGroup" not in out
    assert out.lstrip().startswith("## Next steps")


def test_cards_form_a_tight_list():
    """Blank lines between items make a loose list — each one rendered as a paragraph."""
    out = mdx.to_markdown(CARDS).strip()
    items = [line for line in out.splitlines() if line.startswith("- ")]
    assert len(items) == 2
    body = "\n".join(out.splitlines()[out.splitlines().index(items[0]):])
    assert "\n\n-" not in body, f"loose list:\n{body}"


def test_a_loose_list_outside_a_component_is_left_alone():
    """REGRESSION: tightening the whole page restyled 55 component-free pages — the API
    reference publishes its field lists loose on purpose."""
    source = "- `created_at: string`\n\n- `display_name: string or null`\n"
    assert mdx.to_markdown(source) == source


def test_blank_lines_inside_code_are_preserved():
    source = "Text.\n\n```python\nfirst = 1\n\n\nsecond = 2\n```\n"
    assert "first = 1\n\n\nsecond = 2" in mdx.to_markdown(source)


def test_a_card_without_a_link_keeps_its_title():
    out = mdx.to_markdown('<Card title="Rate limits">Per-model ceilings</Card>')
    assert out.strip() == "- **Rate limits** — Per-model ceilings"


def test_a_card_blurb_keeps_its_inline_code():
    """REGRESSION: stripping code from the blurb deleted content — 17 pages lost words
    like `LanguageModelSession`, which the fidelity check caught."""
    out = mdx.to_markdown('<Card title="Apple Foundation Models" href="https://x/apple">\n'
                          "  Swift package for Apple's `LanguageModelSession` API\n"
                          "</Card>")
    assert "`LanguageModelSession`" in out


def test_admonitions_become_blockquotes():
    """Matches the style the Databricks pages already use, so the corpus reads alike."""
    out = mdx.to_markdown("<Note>\n  Claude Mythos Preview is deprecated.\n</Note>")
    assert "> **Note:**" in out
    assert "> Claude Mythos Preview is deprecated." in out


def test_each_admonition_keeps_its_own_label():
    assert "> **Warning:**" in mdx.to_markdown("<Warning>Careful.</Warning>")
    assert "> **Tip:**" in mdx.to_markdown("<Tip>Handy.</Tip>")


def test_code_group_unwraps_and_keeps_its_fences():
    source = """<CodeGroup>
  ```bash CLI
  ant messages create --model claude-opus-5
  ```

  ```python Python
  import anthropic
  ```
</CodeGroup>"""
    out = mdx.to_markdown(source)
    assert "<CodeGroup>" not in out
    assert "```bash CLI\nant messages create --model claude-opus-5\n```" in out
    assert "```python Python\nimport anthropic\n```" in out


def test_tabs_become_labelled_sections_with_their_code_intact():
    source = """<Tabs>
      <Tab title="macOS / Linux">
        ```bash
        mkdir -p mcp-tunnel/{config,data}
        ```
      </Tab>

      <Tab title="Windows (PowerShell)">
        ```powershell
        Set-Location mcp-tunnel
        ```
      </Tab>
    </Tabs>"""
    out = mdx.to_markdown(source)
    assert "**macOS / Linux**" in out and "**Windows (PowerShell)**" in out
    # dedented: four or more leading spaces would turn the fence into indented code
    assert "```bash\nmkdir -p mcp-tunnel/{config,data}\n```" in out
    assert "```powershell\nSet-Location mcp-tunnel\n```" in out


def test_steps_are_numbered_in_order():
    source = """<Steps>
  <Step title="Define your tool schema">
    Create a JSON schema for your tool's `input_schema`.
  </Step>

  <Step title="Add strict: true">
    Set `"strict": true` as a top-level property.
  </Step>
</Steps>"""
    out = mdx.to_markdown(source)
    assert "**Step 1: Define your tool schema**" in out
    assert "**Step 2: Add strict: true**" in out
    assert out.index("Step 1") < out.index("Step 2")


def test_a_fence_inside_a_step_survives():
    source = """<Steps>
  <Step title="Install">
    ```bash
    pip install anthropic
    ```
  </Step>
</Steps>"""
    out = mdx.to_markdown(source)
    assert "**Step 1: Install**" in out
    assert "```bash\npip install anthropic\n```" in out


def test_accordions_become_labelled_sections():
    out = mdx.to_markdown('<Accordion title="You want a rapid implementation">\n'
                          "  Traditional ML methods require significant resources.\n"
                          "</Accordion>")
    assert "**You want a rapid implementation**" in out
    assert "Traditional ML methods require significant resources." in out


# --- what must NOT be converted -------------------------------------------

def test_a_component_inside_a_code_fence_is_left_alone():
    """A docs page may legitimately *show* the markup it documents."""
    source = "Example:\n\n```mdx\n<Note>\n  Not converted.\n</Note>\n```\n"
    assert mdx.to_markdown(source) == source


def test_an_unknown_component_passes_through_verbatim():
    source = '<HomeJourneyLink href="/docs/en/x">Start here</HomeJourneyLink>'
    assert mdx.to_markdown(source) == source


def test_an_unclosed_component_does_not_swallow_the_page():
    source = "<Tabs>\n  <Tab title=\"One\">\n\n## A later heading\n\nBody text."
    out = mdx.to_markdown(source)
    assert "## A later heading" in out and "Body text." in out


def test_plain_markdown_is_untouched():
    source = "# Title\n\nSome prose with a [link](https://x.com).\n\n- item\n"
    assert mdx.to_markdown(source) == source


def test_nested_components_of_the_same_type_close_correctly():
    source = ('<AccordionGroup>\n'
              '  <Accordion title="Outer">\n'
              '    <Accordion title="Inner">Deep body</Accordion>\n'
              '  </Accordion>\n'
              '</AccordionGroup>')
    out = mdx.to_markdown(source)
    assert "**Outer**" in out and "**Inner**" in out and "Deep body" in out
    assert "<Accordion" not in out


def test_a_self_closing_card_becomes_a_link():
    """`<Card ... />` with no body. Skipping void tags left every link in them inert —
    the release-notes index publishes ten, and the `mdx_converted` invariant caught it
    only because the check was re-run after a refresh."""
    src = ('<Card id="claude-opus-5" title="Claude Opus 5" icon="file" '
           'href="https://x.test/opus-5" />')

    assert mdx.to_markdown(src).strip() == "- [Claude Opus 5](https://x.test/opus-5)"


def test_a_self_closing_unknown_component_is_still_left_alone():
    src = '<HomeJourneyLink to="/somewhere" />'

    assert mdx.to_markdown(src).strip() == src
