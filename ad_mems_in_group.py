import ldap, ldap.async

# Connection information
USERNAME = 'CN=Duong Pham Tung (RAD FTEL),OU=RAD,OU=FTEL HO,OU=FTEL,DC=HO,DC=FPT,DC=VN'
PASSWORD = ''
SERVER   = '10.1.1.51'
BASE     = 'DC=HO,DC=FPT,DC=VN'
GROUP_BASE = 'DC=HO,DC=FPT,DC=VN'
SCOPE    = ldap.SCOPE_SUBTREE
SUFFIX   = '@fpt.com.vn'
ENABLE_ID  = 514
ENABLE_ID2 = 66048 
OUT_FILE = 'list.out'

GROUP_NAME = 'NOC.Admins, VPN Groups'

def get_mems_in_group (ldap_handler, group = GROUP_NAME):
	filter = "(&(objectCategory=group)(objectClass=group)(sAMAccountName={0}))".format (group)
	attributes = ['member']
	timeout    = 0

	s = ldap.async.List (ldap_handler)
	s.startSearch (BASE, SCOPE, filter, attributes)
	s.processResults()
	mems = s.allResults[0][1][1]['member']
	l = [get_user_info (ldap_handler, pcn) for pcn in mems]
	return l

def get_user_info(ldap_handler, cn_name):
	#filter = "(&(sAMAccountName=*)(distinguishedName='{cn}')(|(userAccountControl={id1})(userAccountControl={id2})))".format (cn = cn_name, id1 = ENABLE_ID, id2 = ENABLE_ID2)
	filter = "(&(sAMAccountName=*)(distinguishedName={cn}))".format (cn = gen_filter (cn_name))
	print filter
	attributes = ['sAMAccountName']
	timeout = 0
	res_id = ldap_handler.search (BASE, SCOPE, filter, attributes)
	res_type, res_data = ldap_handler.result (res_id, timeout)
	if res_type == ldap.RES_SEARCH_ENTRY:
		return res_data[0][1]['sAMAccountName'][0]
	else: 
		return None

def write2file (fcontent, fname):
	fhandler = open (OUT_FILE, 'w')
	for pi in fcontent:		
		fhandler.write (pi + SUFFIX + "\n")
	fhandler.close()

def driver():
	ldap_handler = init()
	groups = [pi.strip() for pi in GROUP_NAME.split (',')]
	for pgrp in groups:
		mem_list = get_mems_in_group (ldap_handler, pgrp)
		write2file (mem_list, pgrp + ".out")


# http://msdn.microsoft.com/en-us/library/ms675768.aspx - Creating a Query Filter
# 
def gen_filter (fltr):
	return fltr.replace ('(', '\\28').replace (')', '\\29')

def init():
	try:
		lhandler_ = ldap.open (SERVER)
		lhandler_.simple_bind_s (USERNAME, PASSWORD)
		return lhandler_
	except ldap.LDAPError, error_message:
		print "Could not connect {0}".format (error_message)

if __name__ == "__main__":
	driver()


