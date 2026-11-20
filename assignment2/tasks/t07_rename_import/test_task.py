import users, report, util
assert not hasattr(util, 'normalize')
assert users.key({'name': '  Ada  LOVELACE '}) == 'ada lovelace'
assert report.title(['A  B']) == ['a b']
print('ok')
