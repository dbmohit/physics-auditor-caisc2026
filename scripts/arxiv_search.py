"""
arXiv Search Script for CAISc 2026 Research Pipeline
Usage: python arxiv_search.py --keywords "PINN pollution" --max 20 --output results.json
"""
import urllib.request
import json
import argparse
import re
import time

def search_arxiv(keywords: str, max_results: int = 20, output: str = None):
    query = "+AND+".join(f"all:{w}" for w in keywords.strip().split())
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={query}"
        f"&max_results={max_results}"
        f"&sortBy=submittedDate"
        f"&sortOrder=descending"
    )

    print(f"Searching arXiv: {keywords}")
    with urllib.request.urlopen(url) as response:
        data = response.read().decode("utf-8")

    entries = data.split("<entry>")[1:]
    results = []

    for entry in entries:
        title_match   = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        id_match      = re.search(r"<id>http://arxiv.org/abs/(.*?)</id>", entry)
        author_match  = re.findall(r"<name>(.*?)</name>", entry)
        date_match    = re.search(r"<published>(.*?)</published>", entry)

        results.append({
            "title":    title_match.group(1).strip().replace("\n", " ") if title_match else "",
            "authors":  author_match[:3] if author_match else [],
            "date":     date_match.group(1)[:10] if date_match else "",
            "arxiv_id": id_match.group(1).strip() if id_match else "",
            "url":      f"https://arxiv.org/abs/{id_match.group(1).strip()}" if id_match else "",
            "summary":  summary_match.group(1).strip().replace("\n", " ")[:400] if summary_match else "",
        })

    if output:
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved {len(results)} results to {output}")
    else:
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r['title']}")
            print(f"    Authors: {', '.join(r['authors'])}")
            print(f"    Date: {r['date']} | {r['url']}")
            print(f"    {r['summary'][:200]}...")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search arXiv papers")
    parser.add_argument("--keywords", required=True, help="Search keywords")
    parser.add_argument("--max", type=int, default=20, help="Max results")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    args = parser.parse_args()

    search_arxiv(args.keywords, args.max, args.output)
