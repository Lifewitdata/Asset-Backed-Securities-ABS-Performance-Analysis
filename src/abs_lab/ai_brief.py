"""Optional human-reviewed AI commentary from a small, auditable evidence packet."""
import argparse
import json
import os
import urllib.request
from .pipeline import ROOT


def validate_response(response,facts):
    if not isinstance(response,dict) or set(response)!={"claims"} or not isinstance(response["claims"],list):
        raise ValueError("Expected a claims list")
    for claim in response["claims"]:
        if set(claim)!={"metric_key","value","explanation"}:
            raise ValueError("Unsupported claim fields")
        key=claim["metric_key"]
        if key not in facts or type(claim["value"]) is not type(facts[key]) or claim["value"]!=facts[key]:
            raise ValueError("AI evidence mismatch")
        if not isinstance(claim["explanation"],str):
            raise ValueError("Explanation must be text")
    return response


def run(call_api=False):
    facts=json.loads((ROOT/"reports/research_facts.json").read_text())
    prompt='Explain these simulated research facts without investment advice or invented findings. Return JSON only: {"claims":[{"metric_key":"existing key","value":"exact corresponding typed value","explanation":"brief plain English"}]}. All numbers and keys must match the evidence. Evidence: '+json.dumps(facts)
    (ROOT/"reports/ai_prompt.txt").write_text(prompt+"\n")
    if not call_api:
        print("Evidence prompt written. No AI API called.");return
    key=os.environ["OPENAI_API_KEY"];model=os.environ["ABS_AI_MODEL"]
    body=json.dumps({"model":model,"messages":[{"role":"user","content":prompt}],"response_format":{"type":"json_object"}}).encode()
    request=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=60) as response:
        result=json.load(response)
    parsed=json.loads(result["choices"][0]["message"]["content"])
    checked=validate_response(parsed,facts)
    (ROOT/"reports/ai_commentary_REVIEW_REQUIRED.json").write_text(json.dumps(checked,indent=2)+"\n")
    print("Typed evidence fields validated. Review all free-text claims manually before use.")

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--call-api",action="store_true")
    run(parser.parse_args().call_api)
