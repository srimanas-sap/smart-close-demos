import sys
import json
import argparse

# In-memory mapping data
ACCOUNT_MAPPINGS = {
    "0018000000abcde": "1000329",
    "0018000000xyz12": "1000330",
    "001Ws000053hK4jIAE": "1000329",
    "001Ws000053hK4YIAU": "1000330",
    "001Ws000053hK4HIAU": "1000331",
    "001Ws000053hK4OIAU": "1000332",
    "001Ws000053hK4VIAU": "1000333",
    "001Ws000053hK4QIAU": "1000334",
    "001Ws000053hK4dIAE": "1000335",
    "001Ws000053hK4LIAU": "1000336",
    "001Ws000053hK5MIAU": "1000337",
    "001Ws000053hK4mIAE": "1000338",
    # Account Numbers
    "A83223763": "1000330",
    "A37942334": "1000338",
    "A35771791": "1000333",
    "A32381498": "1000331",
    "A87586863": "1000329",
    "A32501049": "1000332",
    "A89739749": "1000334",
    "A86372801": "1000336",
    "A73896892": "1000335",
    # Account Names
    "Permadyne": "1000330",
    "Permadyne GmbH, LTD": "1000330",
    "Advanced Communications": "1000338",
    "Towson Inc.": "1000333",
    "Towson Inc": "1000333",
    "Southern Solutions": "1000331",
    "Universal Containers": "1000329",
    "Opportunity Resources Inc": "1000332",
    "Employnet": "1000334",
    "Vand Enterprises, Inc.": "1000336",
    "Vand Enterprises": "1000336",
    "Green Fields Media": "1000335",
    "Goodman Imports": "1000335"
}

PRODUCT_MAPPINGS = {
    "B-1000": "TG10",
    "A-100": "TG11",
    "A-1000": "TG12",
    "E-1000": "TG13",
    "A-5000": "TG14",
    "H-36378": "TG15",
    "C-300": "TG16",
    "C-45678": "TG17",
    "M-1000": "TG18",
    "R-100": "TG19",
    "L-1000": "TG20",
    "INST-100": "TG21",
    "L-100": "TG22",
    "S-100": "TG0011",
    "WT-GEN": "TG0012",
    "V-1000": "TG0013",
}

def main():
    parser = argparse.ArgumentParser(description="Translate Salesforce IDs to SAP IDs.")
    parser.add_argument("--type", choices=["account", "product"], help="Translation type: 'account' or 'product'")
    parser.add_argument("--id", help="The Salesforce ID or Product Code to translate")
    parser.add_argument("--accounts", help="Comma-separated list of Salesforce Account IDs")
    parser.add_argument("--products", help="Comma-separated list of Salesforce Product Codes")
    args = parser.parse_args()

    # Multi-item resolution
    if args.accounts or args.products:
        result = {}
        if args.accounts:
            acct_list = [a.strip() for a in args.accounts.split(",") if a.strip()]
            result["accounts"] = {acct_id: ACCOUNT_MAPPINGS.get(acct_id, f"UNKNOWN_{acct_id}") for acct_id in acct_list}
        if args.products:
            prod_list = [p.strip() for p in args.products.split(",") if p.strip()]
            result["products"] = {prod_id: PRODUCT_MAPPINGS.get(prod_id, f"UNKNOWN_{prod_id}") for prod_id in prod_list}
        print(json.dumps(result))
        return

    # Single-item resolution (backwards compatibility)
    if args.type == "account":
        if not args.id or args.id not in ACCOUNT_MAPPINGS:
            print(json.dumps({"error": f"Salesforce Account ID '{args.id}' has no mapped SAP Business Partner ID."}))
            sys.exit(1)
        print(json.dumps({"translated_id": ACCOUNT_MAPPINGS[args.id]}))
    elif args.type == "product":
        if not args.id or args.id not in PRODUCT_MAPPINGS:
            print(json.dumps({"error": f"Salesforce Product Code '{args.id}' has no mapped SAP Material ID."}))
            sys.exit(1)
        print(json.dumps({"translated_id": PRODUCT_MAPPINGS[args.id]}))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
