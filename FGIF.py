import streamlit as st
import pandas as pd
import requests
import time

def search_funders(query):
    """Search OpenAlex for funders matching the query."""
    url = f"https://api.openalex.org/autocomplete/funders?q={query}"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch funders from OpenAlex.")
        return []
    return response.json().get("results", [])

def fetch_grant_ids_for_funder(funder_id, funder_name):
    """Fetch grant IDs where the selected funder is listed among any of the funders (exact name match)."""
    url = f"https://api.openalex.org/works?filter=grants.funder:{funder_id}&per-page=100&cursor=*"
    grant_ids = set()
    total_count = 0
    retrieved_count = 0
    batch_size = 100

    progress_bar = st.progress(0)
    status_text = st.empty()

    while url:
        response = requests.get(url)
        if response.status_code != 200:
            st.error("Failed to fetch grant IDs from OpenAlex.")
            return []

        data = response.json()
        results = data.get("results", [])
        total_count = data.get("meta", {}).get("count", 0)
        retrieved_count += len(results)

        for work in results:
            for grant in work.get("grants", []):
                award_id = grant.get("award_id", "")
                funder_display = grant.get("funder_display_name", "")
                if award_id and funder_display == funder_name:
                    grant_ids.add(award_id)

        progress = min(retrieved_count / max(total_count, 1), 1.0)
        progress_bar.progress(progress)
        status_text.text(f"Fetching grants... {retrieved_count}/{total_count}")

        cursor = data.get("meta", {}).get("next_cursor")
        url = f"https://api.openalex.org/works?filter=grants.funder:{funder_id}&per-page={batch_size}&cursor={cursor}" if cursor else None
        time.sleep(1 / 10)

    progress_bar.empty()
    status_text.text("Fetching complete.")

    if not grant_ids:
        st.warning("No grant IDs found")

    return list(grant_ids)

def main():
    st.title("Funder Grant ID Finder")

    st.markdown("""
    ### **Find Grant IDs by Funder – OpenAlex Explorer**  
    This tool helps you explore research grants associated with specific funders using **OpenAlex**. 
    Simply search for a funder, select one from the list, and retrieve all grant IDs linked to that funder. 
    You can then download the results as a CSV for further analysis.

    **Use cases**:  
    - Identify which grants a funder has supported.  
    - Enrich local research data with grant information.  
    - Cross-reference grants with publications for funding analysis.

    ⚠ **Limitations:**    
    - Some grants may be missing or incorrectly linked due to metadata inconsistencies.  
    - Large funders may have thousands of grants, so fetching data can take time.

    **Looking for publications linked to grants?** Check out this **Publications-Grants Matching Tool**, 
    which finds research output linked to specific grants:  
    🔗 **[Publications-Grants Matching Tool](https://pgmt-tool.streamlit.app/)**

    ### **License:** MIT License

    ### **Creator:** 
    **Søren Vidmar**
    - https://orcid.org/0000-0003-3055-6053  
    - 🏫 Aalborg University
    - 📧 Email: [sv@aub.aau.dk](mailto:sv@aub.aau.dk)  
    - 🏗 GitHub: [github.com/svidmar](https://github.com/svidmar)
    """)

    query = st.text_input("Search for a funder")
    if query:
        funders = search_funders(query)
        if funders:
            selected = st.selectbox("Select a funder", funders, format_func=lambda f: f["display_name"])
            if selected:
                funder_id = selected["id"].split("/")[-1]
                funder_name = selected["display_name"]
                if st.button("Fetch Grant IDs"):
                    grant_ids = fetch_grant_ids_for_funder(funder_id, funder_name)
                    if grant_ids:
                        df = pd.DataFrame({"Grant ID": list(grant_ids)})
                        st.dataframe(df)
                        st.download_button("Download CSV", df.to_csv(index=False), "grant_ids.csv")

if __name__ == "__main__":
    main()
