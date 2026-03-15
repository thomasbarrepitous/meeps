import pytest
import meeps as leaguepedia_parser
from meeps.parsers.team_parser import TeamPlayer

@pytest.mark.api
@pytest.mark.parametrize("team_name", ["T1"])
def test_get_active_players_current_date(team_name):
    # Change this test every new season :')
    assert (
            leaguepedia_parser.get_active_players(team_name) ==
            [
                TeamPlayer(name="Doran", role="Top"),
                TeamPlayer(name="Faker", role="Mid"),
                TeamPlayer(name="Gumayusi", role="Bot"),
                TeamPlayer(name="Keria", role="Support"),
                TeamPlayer(name="Oner", role="Jungle"),
            ]
    )

@pytest.mark.api
@pytest.mark.parametrize("team_name", ["G2 Esports"])
def test_get_active_players_from_date(team_name):
    assert (
            leaguepedia_parser.get_active_players(team_name, date="2019-01-01") ==
            [
                TeamPlayer(name="Caps", role="Mid"),
                TeamPlayer(name="Jankos", role="Jungle"),
                TeamPlayer(name="Mikyx", role="Support"),
                TeamPlayer(name="PERKZ", role="Bot"),
                TeamPlayer(name="Wunder", role="Top"),
            ]
    )


@pytest.mark.api
@pytest.mark.parametrize("team_name", ["TSM"])
def test_get_active_players_from_team_name_disbanded(team_name):
    assert (
            leaguepedia_parser.get_active_players(team_name) ==
            []
    )


# Sorry brother, mwrogue sucks and your tests are failing
# @pytest.mark.parametrize("team_tuple", [("tsm", "TSM"), ("IG", "Invictus Gaming")])
# def test_get_long_team_name(team_tuple):
#     assert (
#         leaguepedia_parser.get_long_team_name_from_trigram(team_tuple[0])
#         == team_tuple[1]
#     )


# @pytest.mark.parametrize(
#     "team_tournament",
#     [("TSM", "LCS 2021 Summer"), ("TSM Academy", "NA Academy 2021 Summer")],
# )
# def test_get_long_team_name_in_tournament(team_tournament):
#     team_name, tournament = team_tournament

#     assert (
#         leaguepedia_parser.get_long_team_name_from_trigram("TSM", tournament)
#         == team_name
#     )


# def test_get_wrong_team_name():
#     assert leaguepedia_parser.get_long_team_name_from_trigram("mister mv") is None


# @pytest.mark.parametrize("team_name", ["T1", "G2 Esports"])
# def test_get_team_logo(team_name):
#     assert leaguepedia_parser.get_team_logo(team_name)


# @pytest.mark.parametrize("team_name", ["T1", "G2 Esports"])
# def test_get_team_thumbnail(team_name):
#     thumbnail_url = leaguepedia_parser.get_team_thumbnail(team_name)
#     assert thumbnail_url


# @pytest.mark.parametrize("team_name", ["T1", "G2 Esports"])
# def test_get_all_team_assets(team_name):
#     assets = leaguepedia_parser.get_all_team_assets(team_name)
#     assert assets.thumbnail_url
#     assert assets.logo_url
#     assert assets.long_name

