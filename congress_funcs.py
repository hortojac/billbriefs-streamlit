import streamlit as st

from congress import Congress
from datetime import datetime, timedelta

@st.cache_resource(ttl=60*60) # Reconnect every 60 minutes
def get_congress_api():
    return Congress(st.secrets["PROPUBLICA_API_KEY"])

@st.cache_data
def get_votes_by_day(chamber, date):
    '''date as string ex "2022-12-21"'''

    return get_congress_api().votes.by_date(chamber, date)

@st.cache_data
def get_vote_details(chamber, rollcall_num, session, congress):
    return get_congress_api().votes.get(
            chamber      = chamber,
            rollcall_num = rollcall_num,
            session      = session,
            congress     = congress,
        )

@st.cache_data
def get_votes_between(chamber, from_dt, to_dt = datetime.today()):
    assert(to_dt > from_dt)

    total_votes = []

    selected_day = to_dt
    delta = timedelta(days=1)

    while selected_day > from_dt:
        date_str = selected_day.strftime('%Y-%m-%d')
        votes_by_day = get_votes_by_day(chamber, date_str)
        total_votes.extend(votes_by_day['votes'])
    
        selected_day -= delta

    return total_votes

@st.cache_data
def process_votes_to_member_positions(votes_list, verbose=False):
    results = {}

    if verbose:
        print("number of votes:", len(votes_list))

    for vote_in_list in votes_list:
        chamber        = vote_in_list['chamber']
        rollcall_num   = vote_in_list['roll_call']
        session        = vote_in_list['session']
        congress_n     = vote_in_list['congress']

        vote_details = get_vote_details(
            chamber      = chamber,
            rollcall_num = rollcall_num,
            session      = session,
            congress     = congress_n,
        )
        
        if "votes" in vote_details:
            if verbose:
                print("number of votes in vote_details:", len(vote_details["votes"]))
                
            if "vote" in vote_details["votes"]:
                vote_result = vote_details["votes"]["vote"]["result"]
                date        = vote_details["votes"]["vote"]["date"]
                time        = vote_details["votes"]["vote"]["time"]
                if "bill" in vote_details["votes"]["vote"]:
                    bill_id = None
                    if "bill_id" in vote_details["votes"]["vote"]["bill"]:
                        bill_id = vote_details["votes"]["vote"]["bill"]["bill_id"]
                if "positions" in vote_details["votes"]["vote"]:
                    positions = vote_details["votes"]["vote"]["positions"]
                    for position in positions:
                        member_id     = position["member_id"]
                        vote_position = position["vote_position"]
                        if member_id not in results:
                            results[member_id] = {}
                        if vote_result not in results[member_id]:
                            results[member_id][vote_result] = []
                        results[member_id][vote_result].append({
                            "bill_id": bill_id,
                            "date": date,
                            "time": time,
                            "vote_position": vote_position,
                            "chamber": chamber,
                            "rollcall_num": rollcall_num,
                            "session": session,
                            "congress": congress_n,
                        })
    return results

@st.cache_data
def build_voting_records(chamber, from_dt, to_dt = datetime.today()):
    all_votes = get_votes_between(chamber, from_dt, to_dt)
    voting_positions_by_member = process_votes_to_member_positions(all_votes)
    return voting_positions_by_member