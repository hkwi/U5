# coding: UTF-8
import logging
import re
import itertools
import lxml.html
import requests

tasks = []
def task(code):
	def proc(func):
		def wrap():
			try:
				gen = func()
				if gen is None:
					return iter([])
				for url in gen:
					assert url
					yield url
			except:
				logging.error("code %s" % code, exc_info=True)
		tasks.append(wrap)
		return wrap
	return proc

def get(url):
	try:
		h = lxml.html.parse(url)
		r = h.getroot()
	except IOError:
		r = lxml.html.document_fromstring(requests.get(url).text, base_url=url)
	
	r.make_links_absolute()
	return r

@task("280003")
def 兵庫県():
	# 兵庫県
	for a in get("https://web.pref.hyogo.lg.jp/kf11/hw10_000000006.html").cssselect("#col_main a"):
		if re.match(r"https://web.pref.hyogo.lg.jp/kf11/documents/.*.pdf", a.get("href", "")):
			yield a.get("href")

@task("281000")
def 兵庫県_神戸市_1():
	# 神戸市
	# 新制度施設一覧
	hit = False
	for a in get("http://www.city.kobe.lg.jp/child/grow/shinseido/index02_02.html").cssselect("#contents a"):
		if re.match(r"https?://www.city.kobe.lg.jp/child/grow/shinseido/.*\.pdf", a.get("href", "")):
			yield a.get("href")
			hit = True
	
	assert hit

@task("281000")
def 兵庫県_神戸市_2():
	# 神戸市
	# 新制度申し込み状況
	hit = False
	for a in get("http://www.city.kobe.lg.jp/child/grow/shinseido/index02_03.html").cssselect("#contents a"):
		if re.match(r"https?://www.city.kobe.lg.jp/child/grow/nursery/img/.*\.pdf", a.get("href", "")):
			yield a.get("href")
			hit = True
	
	assert hit

@task("281000")
def 兵庫県_神戸市_3():
	# 神戸市
	# 認可外施設一覧
	hit = False
	for a in get("http://www.city.kobe.lg.jp/child/grow/nursery/ninkagai/sisetu.html").cssselect("#contents a"):
		if re.match(r"https?://www.city.kobe.lg.jp/child/grow/nursery/ninkagai/.*\.pdf", a.get("href","")):
			yield a.get("href")
			hit = True
	
	assert hit

@task("281000")
def 兵庫県_神戸市_4():
	# 神戸市
	# 施設一覧 HTML
	url = "http://www.city.kobe.lg.jp/child/grow/shinseido/index02_06_1.html"
	yield url
	for a in get(url).cssselect("#contents a"):
		if re.match(r"https?://www.city.kobe.lg.jp/child/grow/nursery/.*\.pdf", a.get("href","")):
			yield a.get("href")

@task("282014")
def 兵庫県_姫路市():
	# 姫路市
	# 施設一覧 HTML
	for a in get("http://www.city.himeji.lg.jp/s50/_25179/_8980.html").cssselect("#mainArea a"):
		if "施設一覧" in a.text:
			yield a.get("href")
	# 認可外保育施設一覧
	yield "http://www.city.himeji.lg.jp/s50/2212387/_5076/_9151.html"

@task("282022")
def amagasaki():
	# 尼崎市
	# 施設一覧
	for a in get("http://www.city.amagasaki.hyogo.jp/kosodate/hoikusyo/index.html").cssselect("#content a"):
		if "保育施設" in a.text:
			for a2 in get(a.get("href")).cssselect("#content a"):
				if a2.text and "一覧" in a2.text:
					yield a2.get("href")

@task("282031")
def akashi():
	# 明石市
	# 市立幼稚園一覧 html
	yield "https://www.city.akashi.lg.jp/kodomo/ikusei_shitsu/yojikyoiku/youchienichiran1.html"
	# 私立はデータベース化されていないので注意
	yield "https://www.city.akashi.lg.jp/kodomo/ikusei_shitsu/yojikyoiku/youjikyouiku.html"
	# 保育所
	yield "https://www.city.akashi.lg.jp/kodomo/ikusei_shitsu/hoiku/hoikushoannai.html"

@task("282049")
def nishinomiya():
	# 西宮市
	for a in get("http://www.nishi.or.jp/print/0002849900030008700514.html").cssselect("#main a"):
		if "一覧" in a.text or "幼稚園について" in a.text:
			yield a.get("href")

@task("282057")
def sumoto():
	# 洲本市
	# 施設一覧（認可保育所・幼稚園・認可外保育施設等）
	for a in get("http://www.city.sumoto.lg.jp/contents/20140724102922.html").cssselect("#container a"):
		if a.text and "一覧" in a.text:
			yield a.get("href")
	# 私立保育園
	# http://www.city.sumoto.lg.jp/hp/reiki/418901010106000000MH/418901010106000000MH/418901010106000000MH.html
	yield "http://www.city.sumoto.lg.jp/hp/reiki/418901010106000000MH/418901010106000000MH/418901010106000000MH_j.html"

@task("282065")
def ashiya():
	# 芦屋市
	# 幼稚園
	for a in get("http://www.city.ashiya.lg.jp/kanri/seido.html").cssselect("#tmp_contents a"):
		if "一覧" in a.text:
			yield a.get("href")
	# 保育園
	for a in get("http://www.city.ashiya.lg.jp/kodomo/hoikusho.html").cssselect("#tmp_contents a"):
		if "一覧" in a.text:
			yield a.get("href")

@task("282073")
def itami():
	# 伊丹市
	# 幼稚園
	for a in get("http://www.city.itami.lg.jp/SOSIKI/EDGAKO/GAKUZI/SYUGAKUEN/index.html").cssselect("#contents a"):
		if "園児募集" in a.text:
			yield a.get("href")
	# 保育所
	for a in get("http://www.city.itami.lg.jp/SOSIKI/KODOMO/HOIKU/").cssselect("#contents a"):
		if "一覧" in a.text:
			for a2 in get(a.get("href")).cssselect("#contents a"):
				if a2.text and "一覧" in a2.text:
					yield a2.get("href")

@task("282081")
def aioi():
	# 相生市
	yield "http://www.city.aioi.lg.jp/soshiki/14.html"
	for a in get("http://www.city.aioi.lg.jp/soshiki/kosodate/kosodatemap2.html").cssselect("#main_body a"):
		if a.text and "マップ" in a.text:
			yield a.get("href")

@task("282090")
def toyooka():
	# 豊岡市
	ct = 0
	for a in get("http://www.city.toyooka.lg.jp/www/genre/0000000000000/1000000001207/index.html").cssselect("#contentsInner a"):
		if a.text == "保育所":
			for a2 in get(a.get("href","")).cssselect("#contentsInner a"):
				if "一覧" in a2.text:
					for a3 in get(a2.get("href","")).cssselect("#contentsInner a"):
						if "一覧" in a3.text:
							yield a3.get("href")
							ct += 1
		elif a.text == "幼稚園":
			for a2 in get(a.get("href","")).cssselect("#contentsInner a"):
				# 市立幼稚園（私立は存在しない？）
				if "入園するとき" in a2.text:
					for a3 in get(a2.get("href","")).cssselect("#contentsInner a"):
						if "一覧" in a3.text:
							yield a3.get("href")
							ct += 1
	
	assert ct==2

@task("282103")
def 兵庫県_加古川市():
	# 兵庫県 加古川市
	# 市立幼稚園
	yield "http://www.city.kakogawa.lg.jp/mokutekibetsudesagasu/nyuen_nyugaku/shiritsuyochien/1415759229773.html"
	# 保育施設
	yield "http://www.city.kakogawa.lg.jp/soshikikarasagasu/kodomo/hoikuka/kosodate_kyoiku/1415865043681.html"
	# 認可外保育施設は兵庫県へ
	# 私立幼稚園？

@task("282120")
def 兵庫県_赤穂市():
	# 兵庫県 赤穂市
	# 幼稚園
	yield "http://www.city.ako.lg.jp/kanko/kyoiku/yochien/"
	# 保育所
	yield "https://www.city.ako.lg.jp/edu/kodomo/nursery_handbook.html"

@task("282138")
def 兵庫県_西脇市():
	# 兵庫県 西脇市
	# 幼稚園
	yield "http://www.city.nishiwaki.lg.jp/lifescenemokutekibetsudesagasu/gakoen/1359271828205.html"
	# 保育所・こども園
	yield "http://www.city.nishiwaki.lg.jp/lifescenemokutekibetsudesagasu/gakoen/hoikusyo/1475192591439.html"

@task("282146")
def 兵庫県_宝塚市():
	# 兵庫県 宝塚市
	# 幼稚園
	yield "http://www.city.takarazuka.hyogo.jp/kyoiku/gakkoshisetsu/1000106/1000552.html"
	# 保育所
	for a in get("http://www.city.takarazuka.hyogo.jp/kyoiku/gakkoshisetsu/1000105/1000540.html").cssselect("#pagebody a"):
		if "一覧" in a.text:
			yield a.get("href")

@task("282154")
def 兵庫県_三木市():
	# 兵庫県 三木市
	# 幼稚園
	yield "http://www2.city.miki.lg.jp/miki.nsf/39f1c87d0d44690349256b000025811d/d38939ba231190d3492571320027a69a?OpenDocument"
	# 保育所
	yield "http://www2.city.miki.lg.jp/miki.nsf/39f1c87d0d44690349256b000025811d/4090b2565376515c49257fd5000f9272?OpenDocument"

@task("282162")
def 兵庫県_高砂市():
	# 兵庫県 高砂市
	yield "http://www.city.takasago.hyogo.jp/index.cfm/14,47730,135,768,html"

@task("282171")
def 兵庫県_川西市():
	# 兵庫県 川西市
	# 幼稚園
	yield "http://www.city.kawanishi.hyogo.jp/kodomo/9780/youchien_ichiran.html"
	# 保育所
	yield "http://www.city.kawanishi.hyogo.jp/kodomo/hoikusyo/h_annai0/index.html"

@task("282189")
def 兵庫県_小野市():
	# 兵庫県 小野市
	# 幼稚園
	yield "http://www.city.ono.hyogo.jp/1/8/43/8/4/2/"
	# 保育所
	yield "http://www.city.ono.hyogo.jp/1/8/13/4/1/"

@task("282197")
def 兵庫県_三田市():
	# 兵庫県 三田市
	# 認可保育所
	yield "http://www.city.sanda.lg.jp/kosodate/kosodate/index.html"
	# 認定こども園
	yield "http://www.city.sanda.lg.jp/kodomoshien/ninteikodomoen.html"
	# 小規模保育
	yield "http://www.city.sanda.lg.jp/kodomoshien/shoukibohoiku28.html"
	# 幼稚園
	url = "http://www.city.sanda.lg.jp/kosodate/kosodate/youchien/index.html"
	yield url
	for a in get(url).cssselect("#col_main a"):
		if a.text.endswith("幼稚園"):
			yield a.get("href")
	# 私立幼稚園
	yield "http://www.city.sanda.lg.jp/kyouiku/shiritsu.html"
	# 認可外保育施設
	yield "http://www.city.sanda.lg.jp/kodomoshien/ninkagai.html"

@task("282201")
def 兵庫県_加西市():
	# 兵庫県 加西市
	# 幼稚園
	yield "http://www.city.kawanishi.hyogo.jp/kodomo/9780/youchien_ichiran.html"
	# 保育所
	yield "http://www.city.kawanishi.hyogo.jp/kodomo/hoikusyo/h_annai0/index.html"

@task("282219")
def 兵庫県_篠山市():
	# 兵庫県 篠山市
	# 幼稚園
	yield "http://www.city.sasayama.hyogo.jp/pc/group/kodomomirai/education/post-2.html"
	# 保育所
	yield "http://www.city.sasayama.hyogo.jp/pc/group/kodomomirai/childbirth/post-9.html"
	# こども園
	yield "http://www.city.sasayama.hyogo.jp/pc/group/kodomomirai/education/post-8.html"

@task("282227")
def 兵庫県_養父市():
	# 兵庫県 養父市
	yield "http://www.city.yabu.hyogo.jp/3691.htm"

@task("282235")
def 兵庫県_丹波市():
	# 兵庫県 丹波市
	# 幼稚園
	yield "http://www.city.tamba.hyogo.jp/site/kosodate/youtienbosyuannai.html"
	# 保育所
	yield "http://www.city.tamba.hyogo.jp/site/kosodate/hoikusyo-list.html"

@task("282243")
def 兵庫県_南あわじ市():
	# 兵庫県 南あわじ市
	yield "http://www.city.minamiawaji.hyogo.jp/soshiki/kosodate/hoikusho.html"

@task("282251")
def 兵庫県_朝来市():
	# 兵庫県 朝来市
	for a in get("http://www.city.asago.hyogo.jp/category/1-3-2-2-0.html").cssselect("#main_naka a"):
		if "一覧" in a.text or re.match(".*年度.*募集.*", a.text):
			yield a.get("href")

@task("282260")
def 兵庫県_淡路市():
	# 兵庫県 淡路市
	# 保育所
	for a in get("http://www.city.awaji.lg.jp/life/2/20/77/").cssselect("#main_body a"):
		if "保育所" in a.text:
			for a2 in get(a.get("href")).cssselect("#main_body a"):
				if "一覧" in a2.text:
					yield a2.get("href")

@task("282278")
def 兵庫県_宍粟市():
	# 兵庫県 宍粟市
	yield "http://www.city.shiso.lg.jp/kurashi/kosodadekyoiku/yotien_hoikusyo/1454286915780.html"

@task("282286")
def 兵庫県_加東市():
	# 兵庫県 加東市
	# こども園・保育所
	yield "http://www.city.kato.lg.jp/kurashi/kosodate/shien/1466986100555.html"
	# 幼稚園
	yield "http://www.city.kato.lg.jp/kurashi/kosodate/1457747773920.html"

@task("282294")
def 兵庫県_たつの市():
	# 兵庫県 たつの市
	for a in get("http://www.city.tatsuno.lg.jp/kurashi/ninshin/index.html").cssselect("#tmp_contents a"):
		if re.match("幼稚園・保育所・(認定)?こども園", a.text):
			yield a.get("href")

@task("283011")
def 兵庫県_猪名川町():
	# 兵庫県 猪名川町
	pass

@task("283657")
def 兵庫県_多可町():
	# 兵庫県 多可町
	pass

@task("283819")
def 兵庫県_稲美町():
	# 兵庫県 稲美町
	pass

@task("283827")
def 兵庫県_播磨町():
	# 兵庫県 播磨町
	pass

@task("284424")
def 兵庫県_市川町():
	# 兵庫県 市川町
	pass

@task("284432")
def 兵庫県_福崎町():
	# 兵庫県 福崎町
	pass

@task("284467")
def 兵庫県_神河町():
	# 兵庫県 神河町
	pass

@task("284645")
def 兵庫県_太子町():
	# 兵庫県 太子町
	pass

@task("284815")
def 兵庫県_上郡町():
	# 兵庫県 上郡町
	pass

@task("285013")
def 兵庫県_佐用町():
	# 兵庫県 佐用町
	pass

@task("285854")
def 兵庫県_香美町():
	# 兵庫県 香美町
	pass

@task("285862")
def 兵庫県_新温泉町():
	# 兵庫県 新温泉町
	# http://www.town.shinonsen.hyogo.jp/d1w_reiki/420901010043000000MH/420901010043000000MH/420901010043000000MH.html
	yield "www.town.shinonsen.hyogo.jp/d1w_reiki/420901010043000000MH/420901010043000000MH/420901010043000000MH_j.html"

if __name__=="__main__":
	for url in itertools.chain(*[t() for t in tasks]):
		print(url)
