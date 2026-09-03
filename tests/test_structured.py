from agents.collector.structured import parse_jsonld


def test_parse_jsonld_job_posting():
    html = """
    <script type="application/ld+json">
    {"@type":"JobPosting","title":"Technical Writer",
     "url":"https://example.com/jobs/1",
     "hiringOrganization":{"name":"Example"},
     "description":"Write documentation."}
    </script>
    """
    jobs = parse_jsonld(html, "example", "https://example.com")
    assert len(jobs) == 1
    assert jobs[0].title == "Technical Writer"
    assert jobs[0].company == "Example"


def test_parse_jsonld_ignores_non_job_schema():
    html = '<script type="application/ld+json">{"@type":"Organization","name":"Example"}</script>'
    assert parse_jsonld(html, "example", "https://example.com") == []
