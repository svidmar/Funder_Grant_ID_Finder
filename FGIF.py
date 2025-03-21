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

def fetch_grant_ids_for_funder(funder_id):
    """Fetch grant IDs associated with a specific funder from OpenAlex."""
    url = f"https://api.openalex.org/works?filter=grants.funder:{funder_id}&per-page=100&cursor=*"
    grant_ids = set()
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_count = 0
    retrieved_count = 0
    batch_size = 100  # Assuming per-page=100 in the API call

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
                if grant.get("award_id"):
                    grant_ids.add(grant["award_id"])
        
        progress_bar.progress(min(retrieved_count / max(total_count, 1), 1.0))
        status_text.text(f"Fetching grants... {retrieved_count}/{total_count}")
        
        cursor = data.get("meta", {}).get("next_cursor")
        url = f"https://api.openalex.org/works?filter=grants.funder:{funder_id}&per-page={batch_size}&cursor={cursor}" if cursor else None
        time.sleep(1 / 10)
    
    progress_bar.empty()
    status_text.text("Fetching complete.")
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
            selected_funder = st.selectbox("Select a funder", [f["display_name"] for f in funders])
            funder_id = next(f["id"] for f in funders if f["display_name"] == selected_funder)
            
            if st.button("Find Grant IDs"):
                grant_ids = fetch_grant_ids_for_funder(funder_id)
                if grant_ids:
                    st.write("### Grant IDs Found:")
                    df = pd.DataFrame(grant_ids, columns=["Grant ID"])
                    st.dataframe(df)
                    
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("Download Grant IDs as CSV", data=csv, file_name="grant_ids.csv", mime="text/csv")
                else:
                    st.write("No grant IDs found for this funder.")

if __name__ == "__main__":
    main()