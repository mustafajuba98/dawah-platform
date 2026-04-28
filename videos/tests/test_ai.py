from unittest.mock import patch

from django.test import TestCase

from videos.management.commands.generate_seo import Command as GenerateSeoCommand
from videos.services.ai_generator import AIDescriptionGenerator


class AIGeneratorTests(TestCase):
    def test_disabled_without_api_key(self):
        generator = AIDescriptionGenerator(api_key="")
        self.assertFalse(generator.enabled)

    @patch("videos.management.commands.generate_seo.AIDescriptionGenerator")
    def test_generate_seo_command_skips_without_key(self, mock_gen):
        instance = mock_gen.return_value
        instance.enabled = False
        command = GenerateSeoCommand()
        command.handle(limit=1)
        instance.bulk_generate.assert_not_called()
