from __future__ import annotations

import unittest
from unittest.mock import patch

from cli.core.generation import fallback_draft, generate_post, parse_title


class GenerationTests(unittest.TestCase):
    def test_parse_title_extracts_first_h1(self) -> None:
        markdown = "intro\n# Hello World\n## Section"
        self.assertEqual(parse_title(markdown), "Hello World")

    def test_parse_title_returns_untitled_without_h1(self) -> None:
        self.assertEqual(parse_title("## No heading"), "Untitled")

    @patch("cli.core.generation.load_ai_config")
    def test_generate_post_uses_fallback_without_api_key(self, mock_load_ai_config) -> None:
        class DummyCfg:
            provider = "openai"
            model = "x"
            api_key = ""

        mock_load_ai_config.return_value = DummyCfg()

        self.assertEqual(generate_post("topic", "audience", "tone", "openai"), fallback_draft())


if __name__ == "__main__":
    unittest.main()
