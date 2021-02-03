#!/usr/bin/python
#coding: utf-8
import sys, re, hashlib, urllib2
from lxml.html import fromstring
from itertools import cycle
import bs4 as bs
reload(sys)
sys.setdefaultencoding('utf-8')


def load_search():
	global data_pmc, aa1, aa3, uspace, months
	global p_space, p_aa1, p_aa3, p_thermo, p_units, p_num, p_vunit, f_terms, b_terms, m_terms
	uspace=u'(\s|\u2000|\u2002|\u2003|\u2004|\u2005|\u2006|\u2007|\u2008|\u2009|\u200a|\u200b|\u200c|\u200d|\u200e|\u200f)'
	p_space= res=re.compile(uspace,re.UNICODE)
	months= {'1': 'Jan', '2':'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun', \
	         '7': 'Jul', '8': 'Aug','9': 'Sep','10': 'Oct','11': 'Nov','12': 'Dec'}
	aa1='ACDEFGHIKLMNPQRSTVWY'
	aa3="ALA|ARG|ASN|ASP|CYS|GLN|GLU|GLY|HIS|ILE|LEU|LYS|MET|PHE|PRO|SER|THR|TRP|TYR|VAL"
	p_aa1 = re.compile(r'(?<=[;:,>\.\s\t\n\(]{1})['+aa1+']{1}\d+['+aa1+']{1}(?=[;:,<\.\s\t\n\)]{1})')
	p_aa3 = re.compile(r'(?<=[;:,>\.\s\t\n\(]{1})((?:'+aa3+'){1}\d+(?:'+aa3+'){1})(?=[;:,<\.\s\t\n\)]{1})',re.IGNORECASE)
	num=u'(?<!\.)\W(?:\d+(?:\.\d+)?(?:\s?(?:\xb1|\u00b1)\s?\d+(?:\.\d+)?)?)\W'
	p_num = re.compile(u'(?<!\.)\W(\d+(?:\.\d+)?(?:\s\u00b1\s\d+(?:\.\d+)?)?)\W',re.UNICODE)
	p_thermo = re.compile(u'(?:\W|^)((?:(?:\u2206|\u0394){1,2}(?:Cp|Tm|UG|GU|G|H|T))|(?:Cp|Tm))', flags=re.UNICODE | re.IGNORECASE )
	units=u'(?:(?:(?:kcal|kj)(?:\/mole?(?:\/[\u00b0|\u00b4]C)?|[\s\*\.\u00b7\u22c5]?(?:mole?[\-\u2212]1)|\/M\/mol|\/\(mol\s[MK]\)|\s[MK][\-\u2212]1)?)|(?:[\u00b0|\u00b4]C))'
	p_units = re.compile(units,flags=re.UNICODE | re.IGNORECASE)
	p_vunit = re.compile(num+units,flags=re.UNICODE | re.IGNORECASE)
	terms='gdmcl|guhcl|gdnhcl|urea|calorimetric|denatura|chevron|two-state|three-state|midpoint|dsc|far-uv|near-uv|molten|refolding|unfolding|m-value'
	terms='two-state|unfolding|denaturant|midpoint|dichroism'
	f_terms = re.compile (u'(?:\W|^)('+terms+')', re.IGNORECASE)
	b_terms = re.compile (u'(?:\W|^)(binding|affinity|dissociation|interaction|ppi|protein-protein|kcat/km)',re.IGNORECASE)
	m_terms = re.compile(u'(?:\W|^)(md simulation|simulation|molecular dynamics|force field|charmm|gromacs|amber|PBSA|GBSA|predict)',re.IGNORECASE)
	data_pmc= ["citation_journal_title","citation_title","citation_authors",\
		  "citation_date","citation_issue","citation_volume","citation_firstpage",\
		  "citation_doi","citation_abstract_html_url","citation_pmid"]
	return



def get_options():
	global pubid, id_type, verbose, elsevier_key
	dinfo={}
	pubid=''
	id_type=''
	url=''
	score=1
	verbose=False
	filename=None
	elsevier_key=''
	ofile=None
	import optparse
	desc = 'Script for parsing html publication pages'
	parser = optparse.OptionParser("usage: [-h] [-p --position] [-l file-ids] ", description=desc)
	parser.add_option('-f','--file', action='store_true',  dest='ifile', help='Local html file')
	parser.add_option('-p','--pmid', action='store_true',  dest='pmid', help='Input pmid')
	parser.add_option('-d','--doi', action='store_true',  dest='doi', help='Input doi')
	parser.add_option('-v','--verbose', action='store_true',  dest='verbose', help='Verbose mode')
	parser.add_option('-s','--score', action='store', type='int', dest='score', default=1, help='Score threshold')
	parser.add_option('-o','--outfile', action='store', type='str', dest='ofile', help='Output file')
	parser.add_option('--ekey','--elsevier-key', action='store', type='str', dest='ekey', help='Elsevier API Key')
	(options, args) = parser.parse_args()
	pubid=args[0]
	if options.pmid:
		pmid=pubid
		id_type='pmid'
		pmc,doi,dinfo=get_pubmed(pubid)
	elif options.doi:
	 	doi=pubid
		id_type='doi'
		pmc,_,dinfo=get_pubmed('"'+pubid+'"')
	elif options.ifile:
		filename=pubid
		pmc,doi,dinfo=get_pubmed(pubid,True)
		if pmc!='':
			id_type='pmc'
			pubid=pmc
			dinfo['pmid']=pmc
		elif doi!='':
			id_type='doi'
			pubid=doi
			dinfo['pmid']=doi
		else:
			id_type='paper'
			pubid='N/A'
			dinfo['pmid']='N/A'
	else:
		pmc=pubid
		id_type='pmc'
		_,doi,dinfo=get_pubmed('PMC'+pubid)
	if id_type=='pmc':
		# USE OPEN ACCESS
		url='https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:'+pmc+'&metadataPrefix=oai'
	elif id_type=='doi':
		url='https://www.doi.org/'+doi
	elif id_type=='pmid':
			if pmc:
				# USE OPEN ACCESS
				url='https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:'+pmc+'&metadataPrefix=oai'
			else:
				url='https://www.doi.org/'+doi
	else:
		pass
	if pmc=='' and doi=='':
		print >> sys.stderr,'ERROR: PMC or DOI ids not found for',pubid
		sys.exit(1)
	if options.score>1: score=options.score
	if options.verbose: verbose=True
	if options.ekey: elsevier_key='APIKey='+options.ekey
	if options.ofile: ofile=options.ofile
	return pubid,url,score,dinfo,filename,ofile


def get_url(url,crossref=False,max_trial=10,max_time=5):
	err=''
	source=''
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding': 'none', 'Accept-Language': 'en-US,en;q=0.8',	'Connection': 'keep-alive'}
	#if crossref: headers['Accept']='text/html,application/xhtml+xml,application/xml,application/vnd.crossref.unixsd+xml;q=0.9,*/*;q=0.8'
	if crossref: headers['Accept']='application/vnd.crossref.unixsd+xml'
	for i in range(max_trial):
		err=''
		source=''
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
		request = urllib2.Request(url, headers=headers)
		try:
			response = opener.open(request, timeout=max_time)
			source = response.read()
			return source,err
		except urllib2.HTTPError, e:
			err='ERROR:'+url+'\n'+str(e)
			print >> sys.stderr,'ERROR:',url,e
		except Exception, e:
			err="ERROR: "+url
			if verbose: print >> sys.stderr,"ERROR:", url
	return source,err


def check_publisher(source):
	url=''
	esource=''
	err=''
	#print source
	soup = bs.BeautifulSoup(source,'lxml')
	ress=soup.find_all('resource')
	for res in ress:
			utext=res.text
			#print utext
			# Elsevier
			if utext.find('?httpAccept=text/plain')>-1 and utext.find('https://api.elsevier.com')>-1:
					url=utext.split('?httpAccept=text/plain')[0]+'?'+elsevier_key
			# Wiley option
			if utext.find('https://onlinelibrary.wiley.com')>-1:
					url='https://onlinelibrary.wiley.com/doi/full/'+pubid
	if len(ress)>0 and url=='':
		# First walue for other publishers
		url=ress[0].text
	if not url:
		ress=soup.find_all('a', href=True)
		for res in ress:
			href=res['href']
			if href.find('https://onlinelibrary.wiley.com/resolve/openurl')>-1: url=href
	if url:
		esource,err=get_url(url)
	#print url,esource
	return esource,err


def check_elsevier(source):
	esource=''
	err=''
	pattern=re.compile('https://api.elsevier.com/content/article/(.*)\?httpAccept=text/plain')
	m=re.findall(pattern,source)
	if len(m)>0:
		url='https://api.elsevier.com/content/article/'+m[0]+'?'+elsevier_key
		esource,err=get_url(url)
	return esource,err


def get_pubmed(pmid,ifile=False):
	pmc=''
	doi=''
	dpmid={'pmid':re.sub(r'^"|"$', '', pmid)}
	pubmed='https://www.ncbi.nlm.nih.gov/pubmed/?term='
	#print pubmed+pmid
	if ifile:
		err=''
		source=''
		try:
			source=open(pmid).read()
		except:
			err='ERROR: File '+pmid+' not found'
	else:
		source,err=get_url(pubmed+pmid,True)
	soup = bs.BeautifulSoup(source,'lxml')
	if source and ifile:
		# XML PMC files
		for sid in soup.find_all('article-id',{'pub-id-type':'pmc'}):
			if sid.text: pmc='PMC'+sid.text
		for sid in soup.find_all('journal-id', {'journal-id-type':"nlm-ta"}):
			if sid.text: dpmid['journal']=sid.text
		if soup.find('article-meta'):
			dvol=''
			auths=''
			sid=soup.find('article-meta')
			if sid.find('pub-date', {'pub-type': "ppub"}):
				child=sid.find('pub-date', {'pub-type': "ppub"})
				if child.find('year'): dvol=dvol+child.year.text
				if child.find('month'): dvol=dvol+' '+months.get(child.month.text,child.month.text)
				if child.find('day'): dvol=dvol+' '+child.day.text
			if sid.find('volume'):
				dvol=dvol+'; '+sid.volume.text
			if sid.find('issue'):
				dvol=dvol+'('+sid.issue.text+')'
			if sid.find('fpage'):
				dvol=dvol+': '+sid.fpage.text
			if sid.find('lpage'):
				dvol=dvol+'-'+sid.lpage.text
			if dvol!='': dpmid['date']=dvol+'.'
			if sid.find('title-group'):
				child=sid.find('title-group')
				if child.find('article-title'):
					title=child.find('article-title').text
					dpmid['title']=title
			for child in sid.find_all('contrib',{'contrib-type': "author"}):
				if child.find('surname'): auths=auths+child.find('surname').text
				if child.find('given-names'): auths=auths+' '+child.find('given-names').text.replace('.','')+', '
			if auths!='': dpmid['authors']=auths[:-2]+'.'

	for a in soup.find_all('a'):
		if a.get('ref',None)=="aid_type=doi":
				doi=a.text
		if a.get('ref',None)=="aid_type=pmcid":
				pmc=a.text.replace('PMC','')
	for d in soup.find_all('div',{'class':"rprt abstract"}):
			for div in d.find_all('div',{'class':'auths'}):
				[sup.extract() for sup in div.findAll('sup')]
				dpmid['authors']=div.text
			for div in d.find_all('div',{'class':'cit'}):
				#dpmid['journal']=div.text
				pinfo=div.text.split('.')
				dpmid['journal']=pinfo[0]+'.'
				dpmid['date']=pinfo[1].strip()+'.'
			for div in d.find_all('h1'):
				dpmid['title']=div.text
	if not dpmid.get('journal',None):
		match=soup.find_all('meta',{'name': "citation_publisher"})
		if len(match)==1: dpmid['journal']=match[0]['content']
	if not dpmid.get('authors',None):
		match=soup.find_all('meta',{'name': "citation_authors"})
		if len(match)==1: dpmid['authors']=match[0]['content'].rstrip(';').replace(';',', ')+'.'
	if not dpmid.get('title',None):
		match=soup.find_all('meta',{'name': "citation_title"})
		if len(match)==1: dpmid['title']=match[0]['content']
	if not dpmid.get('date',None):
		match=soup.find_all('span',{'class': 'cit'})
		if len(match)>0:
			if ifile:
				pinfo=match[0].text.split('.')
				dpmid['journal']=pinfo[0]+'.'
				if len(pinfo)>1 and pinfo[1]!='': dpmid['date']=pinfo[1].strip()+'.'
			else:
				dpmid['date']=match[0].text

	if not dpmid.get('date',None):
		match=soup.find_all('meta',{'name': "citation_date"})
		if len(match)==1: dpmid['date']=match[0]['content']
		match=soup.find_all('meta',{'name': "citation_volume"})
		if len(match)==1:
			if dpmid.get('date',None):
				dpmid['date']=dpmid['date']+'; '+match[0]['content']
			else:
				dpmid['date']=match[0]['content']
		if dpmid.get('date',None): dpmid['date']=dpmid['date']+'.'
	if not doi:
		match=soup.find_all('meta',{'name': "citation_doi"})
		if len(match)>0: doi=match[0]['content']
	if not pmc:
		match=soup.find_all('a',{'class': "id-link"})
		for m in match:
			mtext=m.text.strip().lower()
			if mtext.find('pmc')>-1:
				pmc=mtext.replace('pmc','')
				break
	return pmc,doi,dpmid


def get_data_pmc(sdata):
	dpmc={}
	for m in sdata.find_all('meta'):
		if m.get("name",None) in data_pmc:
			if m.get("content",None): dpmc[m['name'].split("_")[1]]=m['content']
	return dpmc


def get_bio_data(pmc):
	from Bio import Entrez
	dinfo={}
	doi=''
	try:
		Entrez.email = "your.email@google.com"
		handle = Entrez.esummary(db="PMC", id=pmc.replace('PMC',''), retmode="xml")
		records = Entrez.read(handle)
		for record in records:
			dinfo['authors']=', '.join(record.get('AuthorList',[])).rstrip()
			dinfo['title']=record.get('Title','')
			dinfo['date']=record.get('SO', '')
			dinfo['journal']=record.get("FullJournalName", '')
			dinfo['pmid']='PMC'+pmc
			doi=record.get("DOI", '')
	except:
		dinfo['pmid']=pmc
	return pmc,doi,dinfo


def get_table(table):
	tab=[]
	tfoot=[]
	table_rows = table.find_all(['row','tr'])
	for tr in table_rows:
		parent=tr.parent
		if parent.name == 'tfoot' or parent.name =='ce:table-footnote' or parent.name =='ce:caption': continue
		tds = tr.find_all(['td','th','ce:entry','entry'])
		row=[]
		for td in tds:
			row.append(re.sub(r'\ +',' ',re.sub('\r|\n',' ',td.text)).strip())
		tab.append(row)
	granp=table.parent.parent
	if granp.name =='div' and granp.get('class',[''])[0].find('table-wrap')>-1:
		tds= granp.find_all('div',{'class': ['tblwrap-foot','caption']})
		row=[]
		for td in tds:
			row.append(re.sub(r'\ +',' ',re.sub('\r|\n',' ',td.text)).strip())
		tfoot.append(row)
	if table.parent.name == 'table-wrap':
		tds=table.parent.find_all(['table-wrap-foot','caption'])
		row=[]
		for td in tds:
			row.append(re.sub(r'\ +',' ',re.sub('\r|\n',' ',td.text)).strip())
		tfoot.append(row)
	table_tfoot = table.find_all(['tfoot','ce:caption','ce:table-footnote'])
	for tf in table_tfoot:
		tds = tf.find_all(['td','th','ce:entry','entry','ce:note-para','ce:simple-para'])
		row=[]
		for td in tds:
			row.append(re.sub(r'\ +',' ',re.sub('\r|\n',' ',td.text)).strip())
		tfoot.append(row)
	tab=tab+tfoot
	return tab


def get_score(k,d=1):
	s=d
	if k.lower()=='tm' or k.lower()=='cp': s=0
	if k=='Tm' or k=='Cp': s=1
	if k.find(u'\u0394\u0394')>-1 or k.find(u'\u2206\u2206')>-1: s=3
	if k.find(u'\u00b0C')>-1 or k.find(u'\u00baC')>-1: s=1
	if k.find(u'\u00b1')>-1 or k.find(u'\xb1')>-1: s=2
	if k.find('md simulation')>-1: s=-2
	return s


def get_tables(sdata):
	tabs=[]
	did={}
	c=0
	for table in sdata.find_all(['table','ce:table']):
		c=c+1
		s=[0,0,0]
		stable=table.text.decode('utf-8')
		ltable=re.sub(p_space,' ',stable)
		md5=hashlib.md5(stable.encode('utf-8')).hexdigest()
		if did.get(md5,0)!=0: continue
		did[md5]=1
		#print 'Tab:',c
		#print list(set(re.findall(p_thermo,ltable)))
		ts=[0,0,0,0,0]
		tb=0
		l_match=list(set(re.findall(p_thermo,ltable)))
		if len(l_match)>0: ts[0] = sum([get_score(k,2) for k in l_match])
		l_match=list(set(re.findall(p_units ,ltable)))
		if len(l_match)>0: ts[1] = sum([get_score(k,2) for k in l_match])
		l_match=list(set([k.lower() for k in re.findall(f_terms,ltable)]))
		if len(l_match)>0: ts[3] = len(l_match)
		l_match=list(set([k.lower() for k in re.findall(m_terms,ltable)]))
		if len(l_match)>0: ts[4] = sum([get_score(k,-1) for k in l_match])
		tb=len(list(set([m.lower() for m in re.findall(b_terms,ltable)])))
		s[0]=sum(ts)
		s[1]=tb
		s[2]=ts[-1]
		if s[0]>0: #or s[1]>0:
			tab=get_table(table)
			tabs.append([c,s,tab])
		#print c,s
	return tabs,c


def get_divs(sdata):
	tabs=[]
	did={}
	c=0
	for div in sdata.find_all(['p','ce:simple-para','ce:para']):
		c=c+1
		[tab.extract() for tab in div.find_all('table')]
		parent=div.parent
		if parent.get('class',[''])[0] == 'caption': continue
		if parent.name.find('table')>-1 or parent.parent.name.find('table')>-1: continue
		s=[0,0,0]
		sdiv=div.text.decode('utf-8')
		ldiv=re.sub(p_space,' ',sdiv)
		md5=hashlib.md5(sdiv.encode('utf-8')).hexdigest()
		if did.get(md5,0)!=0: continue
		did[md5]=1
		ssdiv=re.split('(?<!Fig|Tab|Ref|\WEq)\.\s[A-Z]',ldiv)
		ts=[0,0,0,0,0]
		tb=0
		l_match=list(set(re.findall(p_thermo,ldiv)))
		if len(l_match)>0:
			#print c,l_match
			ts[0] = sum([get_score(k,2) for k in l_match])
		l_match=list(set(re.findall(p_units ,ldiv)))
		if len(l_match)>0:
			#print c,l_match
			ts[1] = sum([get_score(k,2) for k in l_match])
		l_match=list(set([k.lower() for k in re.findall(f_terms,ldiv)]))
		if len(l_match)>0: ts[3] = len(l_match)
		l_match=list(set([k.lower() for k in re.findall(m_terms,ldiv)]))
		if len(l_match)>0: ts[4] = sum([get_score(k,-1) for k in l_match])
		tb=len(list(set([m.lower() for m in re.findall(b_terms,ldiv)])))
		if sum(ts)>s[0]:
			#print c,ts,udiv
			s[0]=sum(ts)
		if tb>s[1]: s[1]=tb
		s[2]=ts[-1]
		if s[0]>0: #or s[1]>0:
				tabs.append([c,s,div])
		#print c,s
	return tabs,c


def print_table(tab):
	text=''
	for row in tab[2]:
		line='\t'.join([c.encode('utf-8').strip().replace('\n',' ') for c in row])
		if len(line)>0: text=text+pubid+'|Tab:'+str(tab[0])+'|Score:'+str(tab[1][0])+'|Binding:'+str(tab[1][1])+'|'+line+'\n'
	return text.rstrip()


def print_div(div):
	text=''
	if len(div[2].text)>0:
		text=text+pubid+'|Par:'+str(div[0])+'|Score:'+str(div[1][0])+'|Binding:'+str(div[1][1])+'|'+div[2].text.replace('\n',' ')
	return text


def sort_match(l_match):
	s_match=[(len(i),i) for i in list(set(l_match))]
	s_match.sort()
	s_match.reverse()
	return [j for i,j in s_match]


def extract_textdata(source,dinfo,th=1):
	text_out=''
	v_score=['N/A','N/A','N/A','N/A','N/A','N/A']
	dic={}
	tabs=[]
	divs=[]
	l_div=[]
	l_tab=[]
	soup = bs.BeautifulSoup(source,'lxml')
	#get_info(soup)
	if len(dinfo.keys())==0: dinfo=get_data_pmc(soup)
	tabs,nt=get_tables(soup)
	for tab in tabs:
		if tab[1][0]>=th:  #or math.fabs(tab[1][1])>=th:
				l_tab.append(print_table(tab))
				dic['Tab:'+str(tab[0])]=tab[1]
	divs,nd=get_divs(soup)
	for div in divs:
		if div[1][0]>=th: #or math.fabs(div[1][1])>=th:
				l_div.append(print_div(div))
				dic['Par:'+str(div[0])]=div[1]
	if len(dinfo.keys())>0:
		text_out=text_out+'>Authors|'+dinfo.get('authors','N/A')+'\n'
		text_out=text_out+'>Title|'+dinfo.get('title','N/A')+'\n'
		text_out=text_out+'>Journal|'+dinfo.get('journal','N/A')+'\n'
		text_out=text_out+'>Volume|'+dinfo.get('date','N/A')+'\n'
		text_out=text_out+'>ID|'+dinfo.get('pmid','N/A')+'\n'
		v_score[0]=dinfo.get('pmid','N/A')
	if len(l_div)==0 and len(l_tab)==0:
		if len(divs)==0 and len(tabs)==0:
			#print >>sys.stderr,'WARNING: Data not found for',pubid
			##sys.exit(1)
			if nd+nt==0:
				text_out=text_out+'\nERROR: No elements found for the publication '+id_type.upper()+' '+pubid+'. Check if the publication is open access.'
			else:
				text_out=text_out+'\nWARNING: Data not found for the publication '+id_type.upper()+' '+pubid+'.'
		else:
			text_out=text_out+'\nWARNING: No element found in the publication '+id_type.upper()+' '+pubid+' with  scoring threshold '+str(th)+'.'
	else:
		num=len(dic.keys())
		stot1=sum([i for i,j,k in dic.values()])
		stot2=sum([j for i,j,k in dic.values()])
		stot3=sum([k for i,j,k in dic.values()])
		ls=[(j,i) for i,j in dic.items()]
		ls.sort()
		v_score[1]=str(num)
		v_score[2]=str(stot1)
		v_score[3]=str(ls[-1][0][0])
		v_score[4]=str(stot2)
		v_score[5]=str(-stot3)
		text_out=text_out+'>'+'|'.join(['Summary','N:'+str(num),'Total:'+str(stot1),'Binding:'+str(stot2),'Computational:'+str(-stot3),'Max:'+str(ls[-1][0][0])])+'\n'
		text_out=text_out+'\n'.join(l_div)
		text_out=text_out+'\n'
		text_out=text_out+'\n'.join(l_tab)
	return v_score,text_out


def run_shell(pubid,url,score,dinfo,filename=None,ofile=None):
	text_out=''
	if filename:
		try:
			source=open(filename).read()
			err=''
		except:
			source=''
			err='ERROR: File '+filename+' not found.'
			sys.exit(1)
	else:
		source,err=get_url(url,True)
	if err=='':
		esource,err=check_publisher(source)
		if esource!='': source=esource
	if err=='':
		v_score,text_out=extract_textdata(source,dinfo,score)
	if text_out!='':
		if ofile:
			fout=open(ofile,'w')
			fout.write(text_out)
			fout.close()
			print '#PubId  \tN\tTotal\tMax\tBinding\tComputational'
			print '\t'.join(v_score)
		else:
			print text_out


def get_pinfo(dinfo,vinfo=['authors','title','journal','date']):
	pinfo=[]
	for i in vinfo:
		pi=dinfo.get(i,'N/A')
		if pi!='N/A': pi=pi.rstrip('.')+'.'
		pinfo.append(pi)
	return pinfo


if __name__ == "__main__":
	load_search()
	if len(sys.argv)>1:
		pubid,url,score,dinfo,filename,ofile=get_options()
		if len(dinfo.keys())<2 and dinfo.get('pmid',None): pmc,doi,dinfo=get_bio_data(pubid)
		run_shell(pubid,url,score,dinfo,filename,ofile)
	else:
			print 'thermodata.py pmcid'
