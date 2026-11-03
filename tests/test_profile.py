import contextlib
from datetime import date
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from scripts import generate_profile as profile
from scripts.photo_to_ascii import RAMP, photo_to_ascii


ROOT = Path(__file__).resolve().parents[1]
NS = {"svg": "http://www.w3.org/2000/svg"}


def connection(nodes, cursor=None):
    return {
        "nodes": nodes,
        "pageInfo": {"hasNextPage": cursor is not None, "endCursor": cursor},
    }


def history(nodes, total, cursor=None):
    return {"repository": {"defaultBranchRef": {"target": {
        "history": {**connection(nodes, cursor), "totalCount": total},
    }}}}


class AsciiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.photo = Path(self.directory.name) / "photo.png"

    def test_dimensions_ramp_and_brightness(self):
        pixels = np.tile(np.linspace(0, 255, 110, dtype=np.uint8), (120, 1))
        Image.fromarray(pixels).save(self.photo)
        lines = photo_to_ascii(self.photo)
        self.assertEqual(len(lines), 30)
        self.assertTrue(all(len(line) == 55 for line in lines))
        self.assertTrue(set("".join(lines)) <= set(RAMP))
        self.assertTrue(all(line.startswith("@") and line.endswith(" ") for line in lines))

    def test_crop_selects_head_region(self):
        pixels = np.zeros((120, 110), dtype=np.uint8)
        pixels[:, 55:] = 255
        Image.fromarray(pixels).save(self.photo)
        lines = photo_to_ascii(self.photo, crop=(0.5, 0, 1, 1))
        self.assertEqual(set("".join(lines)), {" "})

    def test_aspect_correction_crops_instead_of_stretching(self):
        pixels = np.zeros((100, 200), dtype=np.uint8)
        pixels[:, :50] = 255
        pixels[:, 150:] = 255
        Image.fromarray(pixels).save(self.photo)
        self.assertEqual(set("".join(photo_to_ascii(self.photo))), {"@"})

    def test_subject_is_drawn_with_characters_and_background_is_blank(self):
        Image.new("L", (110, 120), 0).save(self.photo)
        outline = [(0.25, 0.1), (0.75, 0.1), (0.75, 0.9), (0.25, 0.9)]
        lines = photo_to_ascii(self.photo, subject_outline=outline)
        self.assertEqual(lines[0], " " * 55)
        self.assertTrue(all(line[:10] == " " * 10 and line[-10:] == " " * 10 for line in lines))
        self.assertEqual(lines[15][20:35], "@" * 15)

    def test_real_portrait_has_no_background_characters(self):
        config = json.loads((ROOT / "profile.json").read_text())
        lines = photo_to_ascii(ROOT / config["photo"], crop=config["crop"],
                               subject_outline=config["subject_outline"])
        self.assertEqual(lines[0], " " * 55)
        self.assertTrue(all(line[:8] == " " * 8 and line[-8:] == " " * 8 for line in lines[:15]))
        self.assertGreater(sum(character in "#%@" for character in lines[-1]), 30)

    def test_invalid_dimensions_and_crop(self):
        Image.new("L", (20, 20)).save(self.photo)
        for options in ({"columns": 0}, {"rows": -1}, {"crop": (1, 0, 0, 1)},
                        {"crop": (-0.1, 0, 1, 1)}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                photo_to_ascii(self.photo, **options)

    def test_missing_image(self):
        with self.assertRaises(FileNotFoundError):
            photo_to_ascii(self.photo)

    def test_command_prints_exact_grid(self):
        Image.new("L", (100, 100), 0).save(self.photo)
        result = subprocess.run(
            [sys.executable, "-m", "scripts.photo_to_ascii", str(self.photo)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertEqual(result.stdout.splitlines(), ["@" * 55] * 30)


class UptimeTests(unittest.TestCase):
    def test_calendar_years_months_days(self):
        self.assertEqual(profile.calculate_uptime("15-07-2000", date(2026, 11, 3)),
                         "26 years, 3 months, 19 days")

    def test_birthday_and_birth_day(self):
        self.assertEqual(profile.calculate_uptime("03-11-2000", date(2026, 11, 3)),
                         "26 years, 0 months, 0 days")
        self.assertEqual(profile.calculate_uptime("03-11-2026", date(2026, 11, 3)),
                         "0 years, 0 months, 0 days")

    def test_leap_day_and_short_months(self):
        self.assertEqual(profile.calculate_uptime("29-02-2000", date(2023, 2, 28)),
                         "23 years, 0 months, 0 days")
        self.assertEqual(profile.calculate_uptime("31-01-2026", date(2026, 2, 28)),
                         "0 years, 1 months, 0 days")
        self.assertEqual(profile.calculate_uptime("31-01-2026", date(2026, 3, 30)),
                         "0 years, 1 months, 30 days")

    def test_invalid_or_future_date(self):
        for birthday in ("31-02-2000", "2000-01-01", "04-11-2026"):
            with self.subTest(birthday=birthday), self.assertRaises(ValueError):
                profile.calculate_uptime(birthday, date(2026, 11, 3))


class GitHubTests(unittest.TestCase):
    def test_authenticated_graphql_request(self):
        response = contextlib.closing(io.BytesIO(b'{"data": {"user": {"id": "USER"}}}'))
        with patch.object(profile, "urlopen", return_value=response) as send:
            data = profile.github_request("query($login: String!) { user(login: $login) { id } }",
                                          {"login": "example"}, "test-token")
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/graphql")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(json.loads(request.data)["variables"], {"login": "example"})
        self.assertEqual(data["user"]["id"], "USER")
        self.assertGreater(send.call_args.kwargs["timeout"], 0)

    def test_api_errors_do_not_silently_become_zero_stats(self):
        errors = [
            HTTPError("https://api.github.com/graphql", 401, "Unauthorized", {}, None),
            URLError("network unavailable"),
        ]
        self.addCleanup(errors[0].close)
        for error in errors:
            with self.subTest(error=error), patch.object(profile, "urlopen", side_effect=error):
                with self.assertRaises(RuntimeError):
                    profile.github_request("query {}", {}, "secret-token")
        response = contextlib.closing(io.BytesIO(b'{"errors": [{"message": "Rate limit"}]}'))
        with patch.object(profile, "urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "Rate limit"):
                profile.github_request("query {}", {}, "secret-token")

    def test_stats_paginate_repositories_and_authored_history(self):
        responses = [
            {"user": {"id": "USER", "followers": {"totalCount": 7}}},
            {"user": {"repositories": connection([
                {"nameWithOwner": "example/one", "stargazerCount": 3},
            ], "repo-page-2")}},
            {"user": {"repositories": connection([
                {"nameWithOwner": "example/empty", "stargazerCount": 2},
            ])}},
            history([{"additions": 20, "deletions": 4}], 2, "commit-page-2"),
            history([{"additions": 10, "deletions": 2}], 2),
            {"repository": {"defaultBranchRef": None}},
        ]
        with patch.object(profile, "github_request", side_effect=responses) as request:
            stats = profile.fetch_stats("example", "test-token")
        self.assertEqual(stats, {"repos": 2, "commits": 2, "stars": 5,
                                 "followers": 7, "additions": 30, "deletions": 6})
        self.assertEqual(request.call_args_list[2].args[1]["cursor"], "repo-page-2")
        self.assertEqual(request.call_args_list[4].args[1]["cursor"], "commit-page-2")
        self.assertEqual(request.call_args_list[3].args[1]["author"], "USER")
        self.assertIn("isFork: false", request.call_args_list[1].args[0])
        self.assertIn("author:", request.call_args_list[3].args[0])
        self.assertIn("defaultBranchRef", request.call_args_list[3].args[0])

    def test_no_repositories(self):
        responses = [{"user": {"id": "USER", "followers": {"totalCount": 0}}},
                     {"user": {"repositories": connection([])}}]
        with patch.object(profile, "github_request", side_effect=responses):
            self.assertEqual(profile.fetch_stats("example", "token"),
                             dict.fromkeys(("repos", "commits", "stars", "followers",
                                            "additions", "deletions"), 0))

    def test_unknown_user(self):
        with patch.object(profile, "github_request", return_value={"user": None}):
            with self.assertRaisesRegex(RuntimeError, "not found"):
                profile.fetch_stats("missing", "token")


class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "profile.json").read_text())
        self.stats = {"repos": 12, "commits": 1234, "stars": 23,
                      "followers": 45, "additions": 67890, "deletions": 4567}

    def test_both_themes_are_valid_self_contained_svg(self):
        for theme, background in (("dark", "#0d1117"), ("light", "#ffffff")):
            with self.subTest(theme=theme):
                svg = profile.render_svg(self.config, [" .:-=+*#%@".ljust(55)] * 30,
                                         self.stats, theme, date(2026, 11, 3))
                root = ET.fromstring(svg)
                text = "".join(root.itertext())
                self.assertIn(background, svg)
                self.assertIn("itsprateek4510@github", text)
                self.assertIn("prateekkushwaha868@gmail.com", text)
                self.assertIn("1,234", text)
                self.assertIn("+67,890", text)
                self.assertIn("-4,567", text)
                self.assertNotIn("Uptime:", text)
                self.assertNotIn("CarbonSync", text)
                self.assertNotIn("Windows", text)
                self.assertFalse(root.findall(".//svg:image", NS))
                self.assertFalse(root.findall(".//svg:script", NS))
                self.assertFalse(root.findall(".//svg:foreignObject", NS))
                self.assertEqual(len(root.findall(".//svg:text[@id='portrait']/svg:tspan", NS)), 30)
                if theme == "dark":
                    for color in ("#58a6ff", "#3fb950", "#f85149"):
                        self.assertIn(color, svg)

    def test_xml_escaping_and_optional_uptime(self):
        self.config["name"] = 'Prateek <dev> & "friends"'
        svg = profile.render_svg(self.config, ["@" * 55] * 30, self.stats, "dark",
                                 date(2026, 11, 3), "26 years, 0 months, 0 days")
        root = ET.fromstring(svg)
        self.assertIn(self.config["name"], "".join(root.itertext()))
        self.assertIn("Uptime:", "".join(root.itertext()))
        self.assertFalse(root.findall(".//svg:dev", NS))

    def test_portrait_contains_no_stray_preserved_whitespace(self):
        lines = [" @ " + "#" * 52] * 30
        svg = profile.render_svg(self.config, lines, self.stats, "dark", date(2026, 11, 3))
        portrait = ET.fromstring(svg).find(".//svg:text[@id='portrait']", NS)
        self.assertEqual("".join(portrait.itertext()), "".join(lines))

    def test_preview_does_not_invent_stats(self):
        svg = profile.render_svg(self.config, [" " * 55] * 30, None, "light", date(2026, 11, 3))
        self.assertIn("not synced", "".join(ET.fromstring(svg).itertext()))

    def test_entrypoint_generates_both_svgs_and_portrait_from_real_photo(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"GH_TOKEN": "test-token", "PROFILE_BIRTH_DATE": ""}):
                with patch.object(profile, "fetch_stats", return_value=self.stats) as fetch:
                    profile.main(["--output-dir", directory])
            fetch.assert_called_once_with("itsprateek4510", "test-token")
            output = Path(directory)
            lines = (output / "portrait.txt").read_text().splitlines()
            self.assertEqual(len(lines), 30)
            self.assertTrue(all(len(line) == 55 for line in lines))
            self.assertEqual(lines[0], " " * 55)
            self.assertGreater(sum(character in "#%@" for character in lines[-1]), 30)
            for theme in ("dark", "light"):
                root = ET.parse(output / f"{theme}.svg").getroot()
                self.assertIn("1,234", "".join(root.itertext()))

    def test_missing_token_fails_without_overwriting_assets(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SystemExit, "GH_TOKEN"):
                profile.main(["--output-dir", directory])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_authenticated_api_to_svg_integration(self):
        responses = [
            {"user": {"id": "USER", "followers": {"totalCount": 7}}},
            {"user": {"repositories": connection([
                {"nameWithOwner": "itsprateek4510/project", "stargazerCount": 3},
            ])}},
            history([{"additions": 12345, "deletions": 678}], 1),
        ]
        responses = [contextlib.closing(io.BytesIO(json.dumps({"data": data}).encode()))
                     for data in responses]
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"GH_TOKEN": "test-secret", "PROFILE_BIRTH_DATE": ""}):
                with patch.object(profile, "urlopen", side_effect=responses) as send:
                    profile.main(["--output-dir", directory])
            self.assertEqual(send.call_count, 3)
            for call in send.call_args_list:
                self.assertEqual(call.args[0].get_header("Authorization"), "Bearer test-secret")
            for theme in ("dark", "light"):
                svg = (Path(directory) / f"{theme}.svg").read_text()
                self.assertIn("+12,345", svg)
                self.assertIn("-678", svg)
                self.assertNotIn("test-secret", svg)

    def test_api_failure_preserves_existing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in ("dark.svg", "light.svg", "portrait.txt"):
                (output / name).write_text("previous content")
            with patch.dict(os.environ, {"GH_TOKEN": "token", "PROFILE_BIRTH_DATE": ""}):
                with patch.object(profile, "urlopen", side_effect=URLError("offline")):
                    with self.assertRaises(RuntimeError):
                        profile.main(["--output-dir", directory])
            self.assertTrue(all(path.read_text() == "previous content" for path in output.iterdir()))

    def test_preview_never_contacts_github(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(profile, "fetch_stats") as fetch:
                profile.main(["--preview", "--output-dir", directory])
            fetch.assert_not_called()
            self.assertIn("not synced", (Path(directory) / "dark.svg").read_text())

    def test_readme_uses_both_color_schemes(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("<picture>", readme)
        self.assertIn("prefers-color-scheme: dark", readme)
        self.assertIn("prefers-color-scheme: light", readme)
        self.assertIn("assets/dark.svg", readme)
        self.assertIn("assets/light.svg", readme)


if __name__ == "__main__":
    unittest.main()
