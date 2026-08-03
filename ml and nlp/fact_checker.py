"""
=======================================================
  FAKE NEWS ANALYSER — IMPROVED FACT CHECKER
=======================================================
IMPROVEMENT: Smarter Wikipedia fact verification
  - Extracts key entities (names, years, numbers)
  - Checks if specific claims CONTRADICT Wikipedia
  - Detects wrong winners, wrong years, wrong facts
=======================================================
"""

import re
import requests
import wikipedia

wikipedia.set_lang("en")


def extract_key_facts(text: str) -> dict:
    text_lower = text.lower()
    years   = re.findall(r'\b(19|20)\d{2}\b', text)
    numbers = re.findall(r'\b\d+\.?\d*\b', text)
    proper  = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
    actions = re.findall(r'\b(won|lost|founded|invented|created|born|died|elected|appointed|beat|defeated|scored|launched)\b', text_lower)
    return {'years': years, 'numbers': numbers, 'proper': proper, 'actions': actions}


class WikipediaVerifier:

    def verify(self, text: str) -> dict:
        try:
            facts          = extract_key_facts(text)
            search_results = wikipedia.search(text, results=5)
            if not search_results:
                return self._not_found("No Wikipedia article found.")

            best_result = None
            for title in search_results[:3]:
                try:
                    page        = wikipedia.page(title, auto_suggest=False)
                    best_result = (title, page.summary, page.url)
                    break
                except:
                    continue

            if not best_result:
                return self._not_found("Could not load Wikipedia article.")

            title, summary, url = best_result
            summary_lower       = summary.lower()
            text_lower          = text.lower()

            contradictions = []
            supports       = []

            # Year check
            for year in facts['years']:
                if year in summary:
                    supports.append(f"Year {year} confirmed in Wikipedia")
                else:
                    other_years = re.findall(r'\b(19|20)\d{2}\b', summary)
                    if other_years and year not in other_years:
                        contradictions.append(f"Year {year} not confirmed — Wikipedia mentions {', '.join(set(other_years[:3]))}")

            # Proper noun check
            for name in facts['proper']:
                if name.lower() in summary_lower:
                    supports.append(f"'{name}' confirmed in Wikipedia")

            # Winner check — most important
            won_match = re.search(r'(\w+)\s+won', text_lower)
            if won_match:
                claimed_winner = won_match.group(1)
                wiki_won = re.findall(r'(\w+)\s+(?:won|defeated|beat|champion)', summary_lower)
                if wiki_won:
                    if claimed_winner not in [w.lower() for w in wiki_won]:
                        contradictions.append(
                            f"'{claimed_winner.title()}' is NOT confirmed as winner — "
                            f"Wikipedia mentions: {', '.join(set(wiki_won[:3]))}"
                        )
                    else:
                        supports.append(f"'{claimed_winner.title()}' confirmed as winner")

            # Founded by check
            founded_match = re.search(r'(\w+)\s+founded', text_lower)
            if founded_match:
                founder = founded_match.group(1)
                if founder in summary_lower:
                    supports.append(f"'{founder.title()}' confirmed as founder")
                else:
                    wiki_founders = re.findall(r'founded by ([A-Z][a-z]+ [A-Z][a-z]+)', summary)
                    if wiki_founders:
                        contradictions.append(f"Wikipedia says founded by: {', '.join(wiki_founders[:2])}")

            if len(contradictions) > 0:
                verdict = 'contradicted'
            elif len(supports) >= 2:
                verdict = 'supported'
            elif len(supports) == 1:
                verdict = 'partial'
            else:
                verdict = 'unverified'

            return {
                'source': 'Wikipedia', 'found': True, 'verdict': verdict,
                'article': title, 'url': url,
                'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                'supports': supports, 'contradictions': contradictions,
            }

        except wikipedia.exceptions.DisambiguationError as e:
            try:
                summary = wikipedia.summary(e.options[0], sentences=2, auto_suggest=False)
                return {'source': 'Wikipedia', 'found': True, 'verdict': 'partial', 'summary': summary, 'article': e.options[0], 'url': None, 'supports': [], 'contradictions': []}
            except:
                return self._not_found("Multiple topics found.")
        except Exception as e:
            return self._not_found(f"Wikipedia error: {str(e)}")

    def _not_found(self, reason):
        return {'source': 'Wikipedia', 'found': False, 'verdict': 'unverified', 'summary': reason, 'url': None, 'supports': [], 'contradictions': []}


class GoogleFactChecker:

    BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def __init__(self, api_key=None):
        self.api_key = api_key

    def check(self, text):
        if not self.api_key:
            return {'source': 'Google Fact Check', 'found': False, 'verdict': 'skipped', 'reason': 'No API key. Get one free at console.cloud.google.com', 'claims': []}
        try:
            response = requests.get(self.BASE_URL, params={'query': text[:200], 'key': self.api_key}, timeout=5)
            if response.status_code != 200:
                return {'source': 'Google Fact Check', 'found': False, 'verdict': 'error', 'claims': []}
            data   = response.json()
            claims = data.get('claims', [])
            if not claims:
                return {'source': 'Google Fact Check', 'found': False, 'verdict': 'unverified', 'claims': []}
            parsed = []
            for claim in claims[:3]:
                review = claim.get('claimReview', [{}])[0]
                parsed.append({'claim': claim.get('text',''), 'claimant': claim.get('claimant','Unknown'), 'verdict': review.get('textualRating','Unknown'), 'publisher': review.get('publisher',{}).get('name',''), 'url': review.get('url','')})
            ratings  = [c['verdict'].lower() for c in parsed]
            verdicts = {'false':'debunked','fake':'debunked','misleading':'misleading','mostly false':'misleading','true':'supported','mostly true':'supported'}
            overall  = 'unverified'
            for rating in ratings:
                for key, val in verdicts.items():
                    if key in rating:
                        overall = val
                        break
            return {'source': 'Google Fact Check', 'found': True, 'verdict': overall, 'claims': parsed}
        except Exception as e:
            return {'source': 'Google Fact Check', 'found': False, 'verdict': 'error', 'reason': str(e), 'claims': []}


class FactChecker:

    def __init__(self, google_api_key=None):
        self.wikipedia = WikipediaVerifier()
        self.google    = GoogleFactChecker(api_key=google_api_key)

    def check(self, text):
        wiki_result   = self.wikipedia.verify(text)
        google_result = self.google.check(text)
        verdicts      = [wiki_result['verdict'], google_result['verdict']]

        if 'debunked' in verdicts or 'contradicted' in verdicts:
            final, emoji = 'debunked', '🚫'
        elif 'supported' in verdicts:
            final, emoji = 'supported', '✅'
        elif 'misleading' in verdicts:
            final, emoji = 'misleading', '⚠️'
        elif 'partial' in verdicts:
            final, emoji = 'partial', '🔶'
        else:
            final, emoji = 'unverified', '❓'

        return {'final_verdict': final, 'emoji': emoji, 'wikipedia': wiki_result, 'google': google_result}


if __name__ == '__main__':
    checker = FactChecker()
    tests   = [
        "India lose the 2019 ODI World Cup",
        "England won the 2019 Cricket World Cup",
        "Bill Gates founded Microsoft in 1975",
        "Elon Musk founded Apple in 1976",
    ]
    for text in tests:
        print(f"\n📰 {text}")
        r = checker.check(text)
        print(f"   Wikipedia     : {r['wikipedia']['verdict']}")
        if r['wikipedia'].get('contradictions'):
            print(f"   Contradictions: {r['wikipedia']['contradictions']}")
        print(f"   FINAL         : {r['emoji']} {r['final_verdict'].upper()}")