"""
Author: DuongPT3 - FIMHN
Version: 3.0
Date: 13/04/2009
Purpose: 	This is a script for dspam tasks, include querying data from AD, processing data,
			generating file for POSTFIX and inserting data to DB
Libs requirement: python-ldap >= 2.3 and python-ldap < 2.4 
In CentOS 5 families, should install python26-ldap.x86_64 instead of python-ldap.x86_64 in order to work properly
Changelog:
- Create new query to query group from AD
- Modify query to receiving large result from AD
- disable some functions for new purposes of dspam
"""
import ldap, os, datetime, shutil
from ldap.controls import SimplePagedResultsControl

# Log file system
PATH = "" # directory cotains all log files during this running process
ACC_LIST = "all_enable.log" # file cotain all enable accounts on AD server
POSTFIX = "postfix_relay"

# Constant variable for AD query
server = 'xx.xx.xx.xx' # ip/hostname of LDAP Server
user = 'CN=Test01 (),OU=XXX,OU=Special Account,DC=HO,DC=EXAMPLE,DC=VN' # admin account to authenticate in AD
password = 'mysecret' # password to authenticate

DIS_NUM = 514 # the number indicates the disable state of a account
ENA_NUM = 512 # the number indicates the enable state of account
ENA2_NUM = 66048 # fucking id
SUFFIX = "@example.com.vn" # the suffix mail name of each account
BASE = "DC=HO,DC=EXAMPLE,DC=VN" # the start base for searching
GROUP_BASE = "OU=GROUP,DC=HO,DC=EXAMPLE,DC=VN"
SCOPE = ldap.SCOPE_SUBTREE # searching scope in AD

###############################################################################
############################## AD Query #######################################
"""
The initilization of the data query process
Return all file handles of this process
"""
def init_query():
	#if (not os.path.exists (PATH)):
	#	os.mkdir (PATH)
	facc = open (PATH + ACC_LIST, "w")
	return facc

"""
Function gets all group from AD server
Argument: ldap handle, log file handle
return
"""
def getGroupList (ldapHandle, fhandle):
	filter = "(mail=*)"
	attributeList = ['name', 'mail']
	resultSet = []
	timeout = 0
	resultID = ldapHandle.search (GROUP_BASE, SCOPE, filter, attributeList)
	while True:
		resultType, resultData = ldapHandle.result (resultID, timeout)
		if (len (resultData) == 0):
			break
		else:
			if resultType == ldap.RES_SEARCH_ENTRY:
				resultSet.append (resultData)
	if len (resultSet) == 0:
		print "No result \n"
		return
	index = 0
	for pi in range (len (resultSet)):
		for entry in resultSet[pi]:
			index += 1
			accName = entry[1]['name'][0]
			mail    = entry[1]['mail'][0]
			if (accName + SUFFIX).lower() != mail.lower():
					#fhandle.write (accName + "," + mail + "\n")
					print (accName + "," + mail + "\n")
	print "Total of groups: %d: " % index

"""
Function get all enabled account on AD
Argument: ldap handle, log file handle
return
"""
def getEnabledAccountList (ldapHandle, fhandle):
	# define variables for query
	page_size = 1000
	filter = "(&(sAMAccountName=*)(userAccountControl=" + str(ENA_NUM) + "))"
	attributeList = ['sAMAccountName', 'mail']

	lc = SimplePagedResultsControl (ldap.LDAP_CONTROL_PAGE_OID, True, (page_size, ""))
	msgid = ldapHandle.search_ext (
		BASE,
		SCOPE,
		filter,
		attributeList,
		serverctrls = [lc]
	)
	pages = 0
	while True:
		pages += 1
		print "Getting page %d" % pages
		rtype, rdata, rmsgid, serverctrls = ldapHandle.result3 (msgid)
		print "%d results" % len (rdata)

		for pi in rdata:
			if (len (pi) == 2) and (type (pi[1]) is dict) and (len(pi[1]) == 2):
				#print pi
				#print pi[1]
				accName = pi[1]['sAMAccountName'][0]
				mail    = pi[1]['mail'][0]
				if (accName + SUFFIX).lower() != mail.lower():
					#fhandle.write (accName + "," + mail + "\n")
					print (accName + "," + mail + "\n")
		pctrls = [
			c
			for c in serverctrls
			if c.controlType == ldap.LDAP_CONTROL_PAGE_OID
		]

		if pctrls:
			est, cookie = pctrls[0].controlValue
			if cookie:
				lc.controlValue = (page_size, cookie)
				msgid = ldapHandle.search_ext (BASE, SCOPE, filter, attributeList, serverctrls=[lc])
			else:
				break
		else:
			print "Warning"
			break


def getFuckingAccountList (ldapHandle, fhandle):
	# define variables for query
	page_size = 1000
	filter = "(&(sAMAccountName=*)(userAccountControl=" + str(ENA2_NUM) + "))"
	attributeList = ['sAMAccountName', 'mail']

	lc = SimplePagedResultsControl (ldap.LDAP_CONTROL_PAGE_OID, True, (page_size, ""))
	msgid = ldapHandle.search_ext (
		BASE,
		SCOPE,
		filter,
		attributeList,
		serverctrls = [lc]
	)
	pages = 0
	while True:
		pages += 1
		print "Getting page %d" % pages
		rtype, rdata, rmsgid, serverctrls = ldapHandle.result3 (msgid)
		print "%d results" % len (rdata)

		for pi in rdata:
			if len (pi) == 2 and type (pi[1]) is dict:
				accName = pi[1]['sAMAccountName'][0]
				mail    = pi[1]['mail'][0]
				if (accName + SUFFIX).lower() != mail.lower():
					fhandle.write (accName + "\t" + mail + "\n")
		pctrls = [
			c
			for c in serverctrls
			if c.controlType == ldap.LDAP_CONTROL_PAGE_OID
		]

		if pctrls:
			est, cookie = pctrls[0].controlValue
			if cookie:
				lc.controlValue = (page_size, cookie)
				msgid = ldapHandle.search_ext (BASE, SCOPE, filter, attributeList, serverctrls=[lc])
			else:
				break
		else:
			print "Warning"
			break

"""
The main function of query process
"""
def driver_query():
	try:
		ldapHandle = ldap.open (server)

		''' Set ldap connection 's option to support large result and authentication to FPT AD '''
		ldapHandle.set_option (ldap.OPT_REFERRALS, 0)
		ldapHandle.protocol_version = 3

		facc = init_query()
		print "Connecting to LDAP Server: %s" % server
		ldapHandle.simple_bind_s (user, password)
		print "Connected..."
		print "Searching..."
		print "Get All Account..."
		getGroupList (ldapHandle, facc)
		getEnabledAccountList (ldapHandle, facc)
		#getFuckingAccountList (ldapHandle, facc)
		print "Done"
		ldapHandle.unbind_s()
		facc.close()
	except ldap.LDAPError, error_message:
		print "LDAP error %s" % error_message
	except IOError, error_message:
		print error_message

###############################################################################

###############################################################################
############################ Generate Postfix file ############################
"""
Write content to file
Argument: file handle, content to be written
"""
def write2file (fhandle, fcontent):
	for pi in fcontent:
		tmp = pi[0 : len (pi) - 1]
		fhandle.write (tmp + "\n")

def formatPostfix (li):
	res = []
	for pi in li:
		tmp = str.lower (pi[0 : len(pi) - 1])
		i = tmp.index ("@", 0, len (tmp))
		tmp += " " + str.lower (pi[0 : i]) + "\n"
#		tmp += " dummy\n"
		res.append (tmp)
	return res

def driver_postfix():
	f = open (PATH + ACC_LIST, "r")
	accList = f.readlines()
	accList = formatPostfix (accList)
	f.close()
	f = open (PATH + POSTFIX, "w")
	write2file (f, accList)

###############################################################################

if __name__ == "__main__":
	print "Querying data"
	driver_query()
	print "Done...\n"

	#print "Generating Postfix file"
	#driver_postfix()
	#print "Done...\n"
