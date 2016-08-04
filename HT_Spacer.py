#MenuTitle: HT Spacer
# Version 1.0.0
# Created by Andres Torresi, (Huerta Tipografica)
# This script can only be used with authorization
# The program will be useful assigning it a shortcut in OSX keyboard preferences.

#  Basic config
# if window=True, scripts run with a UI
window=False
# Tabular: if True doesn't change glyph widths // It is automatic for .tf or .tosf glyphs
tabVersion=False

# Default parameters
paramArea = 400 #white area in thousand units
paramDepth = 15 #depth in open counterforms, from extreme points. 
paramOver = 0 #overshoot in spacing vertical range

# ADVANCED CONFIG
# mark color
color = 1
# creates -areas- glyph, with a drawing of the white space in letter. Requires robofab.
createProofGlyph = False
# frequency of vertical measuring. Higher values are faster but less accurate
freq = 10




# program
#  Dependencies
import GlyphsApp
import math
import numpy as np
import vanilla

if createProofGlyph == True:
	from objectsGS import *
	f=CurrentFont()

GLYPHSAPPVERSION = NSBundle.bundleForClass_(GSMenu).infoDictionary().objectForKey_("CFBundleShortVersionString")
if GLYPHSAPPVERSION.startswith("1."):
	measurementTool = NSClassFromString("GlyphsToolMeasurement").alloc().init()
else:
	measurementTool = NSClassFromString("GSGuideLine")


#  Functions

# file
def fileLocation():
	path = Glyphs.font.filepath.split('/')
	del path[len(path)-1]
	output=''
	for f in path:
		output+=f+'/'
	return output

def config():
	path=fileLocation()
	filename=Glyphs.font.filepath.split('/')
	filename=filename[-1].split('.')
	filename=filename[0]
	filename = path+filename+"_autospace.py"
	array = []
	with open(filename) as f:
		for line in f:
			if line[0]!='#' and len(line) > 5:
				newline=line.split(",")
				del newline[-1]	
				newline[3]=float(newline[3])
				array.append(newline)
	return array

# get layer id
def layerIndex(font,layer):
	actualId=layer.layerId
	for i in range(len(font.masters)):
		if actualId==font.masters[i].id:
			index=i
	return index

def autoAlignment( thisLayer ):
	status=False
	for thisComp in thisLayer.components:
		# print thisComp.disableAlignment
		if thisComp.disableAlignment == True:
			status = True
	if len(thisLayer.components)>0 and len(thisLayer.paths) == 0 and status==False:
		make=False
	else:
		make=True
	return make


def setSidebearings(color,font,glyphList):
	for g in glyphList:
		font.glyphs[g[1]].layers[g[0]].LSB=g[2]
		font.glyphs[g[1]].layers[g[0]].RSB=g[3]

		#ajusta el error de calculo tabular
		if g[4]!=False:
			font.glyphs[g[1]].layers[g[0]].width=g[4]

		if color!=False:
			font.glyphs[g[1]].color=color

# shape calculations
def rectCateto(angle, cat):
    angle = math.radians(angle)
    result = cat * (math.tan(angle))
    #result = round(result)
    return result

def rectHipotenusa(cat1, cat2):
    result = math.sqrt((cat1 ** 2 + cat2 ** 2))
    return result

def rectAngle(cat1, cat2):
    angle = math.atan(cat1 / cat2)
    return math.degrees(angle)

# polygon area
def areaPoligono(x, y):
    ind_arr = np.arange(len(x))-1  # for indexing convenience
    s = 0
    for ii in ind_arr:
        s = s + (x[ii] * y[ii + 1] - x[ii + 1] * y[ii])

    return abs(s) * 0.5

# point list area
def area(points):
    arrayx = []
    arrayy = []

    for p in range(len(points)):
        point = points[p]
        arrayx.append(point[0])
        arrayy.append(point[1])
    return areaPoligono(arrayx, arrayy)


# returns horizontal, vertical range
def amplitude(layer):
    return layer.box[2]-layer.box[0],layer.box[3]-layer.box[1],

# get margins in robofab
# def getMargins(layer, y):
# pen = MarginPen(layer.getParent(), y, True)
# layer.draw(pen)
# # get crossing values
# crossings = pen.getMargins()
# try:
#     margins = (crossings[0], crossings[1])
# except:
#     margins = (None, None)
# return margins

# get margins in Glyphs
def getMargins(layer,y):

	#works over glyph copy
	cleanLayer = layer.copyDecomposedLayer()
	cleanLayer.removeOverlap()
	cleanLayer.addExtremePointsForce_(True)

	layer = cleanLayer

	startPoint = NSMakePoint(-1000, y)
	endPoint = NSMakePoint(3000, y)

	if GLYPHSAPPVERSION.startswith("2."):
		result = layer.calculateIntersectionsStartPoint_endPoint_( startPoint, endPoint )
	else:
		result = measurementTool.calculateIntersectionsForLayer_startPoint_endPoint_(layer, startPoint, endPoint)

	puntos=len(result)
	left=1
	right=len(result)-2

	if (puntos>2):
		margins=(result[left].pointValue().x,result[right].pointValue().x)
	else:
		margins=(None,None)
	return margins

# a list of margins
def marginList(layer, bottom, top):
	y = bottom
	listL = []
	listR = []
	while y <= top:
		margins = getMargins(layer, y)
		lpos = margins[0]
		rpos = margins[1]
		listL.append([lpos, y])
		listR.append([rpos, y])
		y = y + freq

	lista = [listL, listR]
	return lista

def marginsZone(margins,bottom,top):
	marginsNew=[[],[]]
	for index in range(len(margins[0])):
		if margins[0][index][1]>=bottom and margins[0][index][1]<=top:
			marginsNew[0].append(margins[0][index])
			marginsNew[1].append(margins[1][index])
	return marginsNew


# sets depth for each point in list
# left
def setDepthInListL(lista,depth,puntosExtremos):
    list= []
    for p in lista:
        #si es nulo lo pone a la profundiad
        if p[0] != None:
            x=p[0]
            if p[0] > (puntosExtremos[0][0]+depth):
                x=puntosExtremos[0][0]+depth
        else:
            x=puntosExtremos[0][0]+depth
        list.append([x,p[1]])
    return list

# right
def setDepthInListR(lista,depth,puntosExtremos):
    list= []
    for p in lista:
        if p[0] != None:
            x=p[0]
            if p[0] < (puntosExtremos[1][0]-depth):
                x=puntosExtremos[1][0]-depth
        else:
            x=puntosExtremos[1][0]-depth
        list.append([x,p[1]])
    return list


# creates proof glyph
def createAreasGlyph(font,origenLayer,layerIndex,margins):
	from robofab.pens.marginPen import MarginPen
	if f.has_key('areas'):
		areaLayer=font.glyphs['areas'].layers[layerIndex]
		#f.removeGlyph('areas')
		#del font.glyphs["areas"]
		#removeSegment(index)

		for i in range( len( areaLayer.paths ))[::-1]:
			del areaLayer.paths[i]
	else:
		f.newGlyph("areas")
	origen=f[origenLayer.parent.name]

	drawArea(origen, f['areas'], margins[0])
	drawArea(origen, f['areas'], margins[1])


# draw outlines on areas glyph
def drawArea(origen, destination, puntos):
    destination.width = origen.width
    #pen
    pen = destination.getPen()

    # Tell the pen to draw things
    pen.moveTo(puntos[0])
    for p in puntos:
        pen.lineTo(p)

    # Done drawing: close the path
    pen.closePath()
    print destination
    # destination.update()



class htSpacer( object ):
	def __init__( self ):
		self.font = Glyphs.font
		selectedLayers = Glyphs.currentDocument.selectedLayers()
		self.mySelection=list(set(selectedLayers))
		self.output=''
		self.layerIndex = layerIndex(self.font,self.mySelection[0])
		self.master=self.font.masters[self.layerIndex]

		self.angle=self.master.italicAngle
		self.x=self.master.xHeight
		self.mline=self.master.xHeight/2

		self.getParams()
		self.paramDepth=int(self.paramDepth)
		self.paramOver=int(self.paramOver)

		self.tab=False
		self.LSB=True
		self.RSB=True

		self.glyphValues=[]

		if window==True:
			self.window()
		else:
			self.spaceMain(self)

	def getParams(self):
		if self.font.masters[self.layerIndex].customParameters["paramArea"]:
			self.paramArea=self.font.masters[self.layerIndex].customParameters["paramArea"]
			self.output+='Using master custom parameter, paramArea: '+str(self.paramArea)+"\n"
		else:
			self.paramArea=paramArea
			self.output+='Using DEFAULT PARAMETERS, paramArea: '+str(self.paramArea)+"\n"
		if self.font.masters[self.layerIndex].customParameters["paramDepth"]:
			self.paramDepth=self.font.masters[self.layerIndex].customParameters["paramDepth"]
			self.output+='Using master custom parameter, paramDepth: '+str(self.paramDepth)+"\n"
		else:
			self.paramDepth=paramDepth
			self.output+='Using DEFAULT PARAMETERS, paramDepth: '+str(self.paramDepth)+"\n"
		if self.font.masters[self.layerIndex].customParameters["paramOver"]:
			self.paramOver=self.font.masters[self.layerIndex].customParameters["paramOver"]
			self.output+='Using master custom parameter, paramOver: '+str(self.paramOver)+"\n"
		else:
			self.paramOver=paramOver
			self.output+='Using DEFAULT PARAMETERS, paramOver: '+str(self.paramOver)+"\n"


	def setG(self,layer):
		self.output='\\'+layer.parent.name+'\\'+"\n"+self.output
		self.glyph=layer.parent
		self.layer=layer
		self.category=layer.parent.category
		self.subCategory=layer.parent.subCategory
		self.script=layer.parent.script
		self.reference=self.glyph.name
		self.exception=self.findException()
		if self.exception:
			print self.exception

		self.area=float(self.paramArea)*100

		self.minYref=0
		self.maxYref=0
		self.minYg=0
		self.maxYg=0

		self.newL=layer.LSB
		self.newR=layer.RSB
		self.newWidth=False


	def window( self ):

		self.w = vanilla.FloatingWindow( (250, 200), "AutoEspaciar", minSize=(225, 200), maxSize=(225, 200), autosaveName="com.ht.spacer" )
		self.w.text_3 = vanilla.TextBox( (210, 25, -170, 14), "%", sizeStyle='small' )
		self.w.text_4 = vanilla.TextBox( (15, 50, 100, 14), "Area", sizeStyle='small' )
		self.w.text_4b = vanilla.TextBox( (140, 50, 50, 14), self.paramArea, sizeStyle='small' )
		self.w.text_5 = vanilla.TextBox( (15, 75, 100, 14), "Profundidad", sizeStyle='small' )
		self.w.text_5b = vanilla.TextBox( (140, 75, 50, 14), self.paramDepth, sizeStyle='small' )
		self.w.text_6 = vanilla.TextBox( (15, 100, 100, 14), "Excedente", sizeStyle='small' )
		self.w.text_6b = vanilla.TextBox( (140, 100, 50, 14), self.paramOver, sizeStyle='small' )
		self.w.LSB = vanilla.CheckBox( (15,    25, 40, 18), "LSB", value=True, sizeStyle='small', callback=self.SavePreferences )
		self.w.RSB = vanilla.CheckBox( (15+45, 25, 40, 18), "RSB", value=True, sizeStyle='small', callback=self.SavePreferences )
		self.w.tab = vanilla.CheckBox( (15+45+45, 25, 60, 18), "Tabular", value=False, sizeStyle='small', callback=self.SavePreferences )
		self.w.ancho = vanilla.EditText( (170, 25, 40, 18), self.mySelection[0].width, sizeStyle = 'small')
		self.w.area = vanilla.EditText( (170, 50-3, 40, 18), "430", sizeStyle = 'small')
		self.w.prof = vanilla.EditText( (170, 75-3, 40, 18), "20", sizeStyle = 'small')
		self.w.ex = vanilla.EditText( (170, 100-3, 40, 18), "0", sizeStyle = 'small')

		self.w.runButton    = vanilla.Button((15,    125, 90, 25), "Aplicar", sizeStyle='small', callback=self.spaceMain )

		self.w.setDefaultButton( self.w.runButton )

		if not self.LoadPreferences():
			print "Error: Could not load preferences. Will resort to defaults."

		self.w.open()

	def SavePreferences( self, sender ):
		try:
			Glyphs.defaults["com.ht.spacer.LSB"] = self.w.LSB.get()
			Glyphs.defaults["com.ht.spacer.RSB"] = self.w.RSB.get()
			Glyphs.defaults["com.ht.spacer.tab"] = self.w.tab.get()
			Glyphs.defaults["com.ht.spacer.area"] = self.w.area.get()
			Glyphs.defaults["com.ht.spacer.depth"] = self.w.prof.get()
			Glyphs.defaults["com.ht.spacer.over"] = self.w.ex.get()
		except:
			return False

		return True

	def LoadPreferences( self ):
		try:
			self.w.LSB.set( Glyphs.defaults["com.ht.spacer.LSB"] )
			self.w.RSB.set( Glyphs.defaults["com.ht.spacer.RSB"] )
			self.w.tab.set( Glyphs.defaults["com.ht.spacer.tab"] )
			self.w.area.set( Glyphs.defaults["com.ht.spacer.area"] )
			self.w.prof.set( Glyphs.defaults["com.ht.spacer.depth"] )
			self.w.ex.set( Glyphs.defaults["com.ht.spacer.over"] )
		except:
			return False

		return True
# progress bar
	def progressBar(self):
		self.p = vanilla.Window((300, 40))
		self.p.bar = vanilla.ProgressBar((10, 10, -10, 16))
		self.p.open()
		self.p.bar.set(0)
		self.wunit=100.000/len(self.mySelection)

	def findException(self):
		exception=False
		items=[]
		for item in config():
			if self.script == item[0] or item[0] == '*':
				if self.category == item[1] or item[1] == '*':
					if self.subCategory == item[2] or item[2] == '*':
						items.append(item)
						
		if len(items)>0:
			exception=items[0]
			for item in items:
				if item[5] in self.glyph.name:
					exception=item

		return exception

	def setResize(self):
		if(self.exception):
			self.area=self.area*self.exception[3]



	def setReference(self):
		if(self.exception):
			item = self.exception
			if item[4]!='*':
				self.reference=item[4]

	#calculates distance over and below
	def excedente(self):
	    valorExcedente = self.x * self.paramOver/100
	    return valorExcedente

	def box(self,layer):
	    return layer.bounds[0][0],layer.bounds[0][1],layer.bounds[1][0]+layer.bounds[0][0],layer.bounds[0][1]+layer.bounds[1][1]

	def maxPoints(self,list,minY,maxY):
		right = -10000
		left = 10000
		for p in list:
			if p[1] >= minY and p[1] <= maxY:
			   if p[0] > right and p[0]!=None:
			       right = p[0]
			       righty = p[1]
			   if p[0] < left and p[0]!=None:
			       left = p[0]
			       lefty = p[1]

		return ((left, lefty),(right,righty))

	def layerExtremes(self,layer):
		points=[]
		for path in layer.paths:
			for node in path.nodes:
				if node.type!=65:
					points.append((node.x,node.y))
		points.sort()
		return points[0],points[-1]

	def processMargins(self,margins):
		#deSlant if is italic
		margins=self.deSlant(margins)
		#get extremes
		puntosExtremos = self.maxPoints(margins[0]+margins[1],self.minYref,self.maxYref)

		#set depth
		margins=self.setDepth(margins[0],margins[1],puntosExtremos)
		#close open counterforms at 45 degrees
		margins=self.diagonize(margins[0],margins[1])
		margins=self.closeOpenCounters(margins[0],margins[1],puntosExtremos)
		margins=self.slant(margins)
		return margins[0],margins[1]

	#process lists with depth, proportional to xheight
	def setDepth(self,marginsL,marginsR,puntosExtremos):
		depth     = self.x * self.paramDepth/100
		marginsL  = setDepthInListL(marginsL,depth,puntosExtremos)
		marginsR  = setDepthInListR(marginsR,depth,puntosExtremos)
		return marginsL,marginsR

	#close counterforms at 45 degrees
	def diagonize(self,marginsL,marginsR):
	    total=len(marginsL)-1

	    valueFreq=freq*1.5
	    for index in range(total):
	        #left
	        actualPoint = marginsL[index]
	        nextPoint = marginsL[index + 1]
	        if nextPoint[0] > (actualPoint[0] + valueFreq) and nextPoint[1] > actualPoint[1]:
	            marginsL[index+1][0] = actualPoint[0] + valueFreq
	        #right
	        actualPoint = marginsR[index]
	        nextPoint = marginsR[index + 1]
	        if nextPoint[0] < (actualPoint[0] - valueFreq) and nextPoint[1] > actualPoint[1]:
	            marginsR[index+1][0] = actualPoint[0] - valueFreq

	        #left
	        actualPoint = marginsL[total-index]
	        nextPoint = marginsL[total-index-1]
	        if nextPoint[0] > (actualPoint[0] + valueFreq) and nextPoint[1] < actualPoint[1]:
	            marginsL[total-index-1][0] = actualPoint[0] + valueFreq
	        #right
	        actualPoint = marginsR[total-index]
	        nextPoint = marginsR[total-index-1]
	        if nextPoint[0] < (actualPoint[0] - valueFreq) and nextPoint[1] < actualPoint[1]:
	            marginsR[total-index-1][0] = actualPoint[0] - valueFreq

	    return marginsL,marginsR

	#close counterforms, creating a polygon
	def closeOpenCounters(self,marginsL,marginsR,puntosExtremos):
	    initPoint=puntosExtremos[0][0],self.minYref
	    endPoint=puntosExtremos[0][0],self.maxYref
	    marginsL.insert(0,initPoint)
	    marginsL.append(endPoint)

	    initPoint=puntosExtremos[1][0],self.minYref
	    endPoint=puntosExtremos[1][0],self.maxYref
	    marginsR.insert(0,initPoint)
	    marginsR.append(endPoint)
	    return marginsL,marginsR

	def italizePoint(self,p):
		if p[0] != None:
			px=p[0]
			py=p[1]
			cateto=self.mline-p[1]
			xvar=-rectCateto(self.angle,cateto)
			p=[px+xvar,py]
		return p

	def deItalizePoint(self,p):
	    if p[0] != None:
	        px=p[0]
	        py=p[1]
	        cateto=p[1]-self.mline
	        xvar=-rectCateto(self.angle,cateto)
	        #xvar=-round(rectCateto(angle,cateto))
	        p=[px+xvar,py]
	    return p

	def deSlant(self,margins):
		if self.angle>0:
			for index in range(len(margins[0])):
				margins[0][index]=self.deItalizePoint(margins[0][index])
				margins[1][index]=self.deItalizePoint(margins[1][index])
		return margins

	def slant(self,margins):
	    for index in range(len(margins[0])):
	        margins[0][index]=self.italizePoint(margins[0][index])
	        margins[1][index]=self.italizePoint(margins[1][index])
	    return margins

	def calcularValorSb(self,poligono):
		amplitudeY = self.maxYref-self.minYref
		#calculates proportional area
		areaProporcional = (amplitudeY * self.area) / self.x
		areaPoligono = area(poligono)
		valor = areaProporcional-areaPoligono
		nuevoValor = valor / amplitudeY
		return nuevoValor

	def setSpace(self):
		self.setResize()
		self.setReference()

		#get reference glyph, if exists
		reference=self.reference
		

		#check reference layer existance and contours
		if self.font.glyphs[reference]:
			referenciaLayer=self.font.glyphs[reference].layers[self.layerIndex]
			if len(referenciaLayer.paths)<1:
				self.output+="WARNING: The reference glyph declared ("+self.reference+") doesn't have contours. Glyph "+self.layer.parent.name+" was spaced uses its own vertical range.\n"
				referenciaLayer=self.layer
		else:
			referenciaLayer=self.layer
			self.output+="WARNING: The reference glyph declared ("+self.reference+") doesn't exist. Glyph "+self.layer.parent.name+" was spaced uses its own vertical range.\n"


		#get reference glyph maximum points
		maxpoints = self.box(referenciaLayer)
		valorExcedente = self.excedente()

		#store min and max y 
		self.minYref = maxpoints[1]-valorExcedente
		self.maxYref = maxpoints[3] + valorExcedente

		#bounds
		box=self.box(self.layer)

		#all the margins
		marginsOne = marginList(self.layer, box[1], box[3])

		#creates a list with left and right margins
		marginsFull = [marginsOne[0],marginsOne[1]]

		#filter values between min and max
		margins = marginsZone(marginsFull,self.minYref,self.maxYref)

		#create a closed polygon
		poligonos=self.processMargins(margins)

		#get area from each side
		areaL=area(poligonos[0])
		areaR=area(poligonos[1])

		#deitalize margins
		marginsFull = self.deSlant(marginsFull)
		#get extreme points deitalized
		extremosFull = self.maxPoints(marginsFull[0]+marginsFull[1],box[1],box[3])
		#get zone extreme points
		extremos = self.maxPoints(margins[0]+margins[1],self.minYref,self.maxYref)

		#dif between extremes full and zone
		distanciaL=math.ceil(extremos[0][0]-extremosFull[0][0])
		distanciaR=math.ceil(extremosFull[1][0]-extremos[1][0])

		#set new sidebearings
		self.newL=math.ceil(0-distanciaL+self.calcularValorSb(poligonos[0]))
		self.newR=math.ceil(0-distanciaR+self.calcularValorSb(poligonos[1]))

		#tabVersion
		if '.tosf' in self.glyph.name or '.tf' in self.glyph.name or self.tab==True or tabVersion==True:
			if window==False:
				self.ancho=self.layer.width
			anchoForma=extremosFull[1][0]-extremosFull[0][0]
			anchoActual=anchoForma+self.newL+self.newR
			anchoDiff=(self.ancho-anchoActual)/2

			self.newL+=anchoDiff
			self.newR+=anchoDiff
			self.newWidth=self.ancho

			self.output+=self.glyph.name+' Fue ajustado tabularmente a '+str(self.ancho)
		#fin tabVersion

		#if there is a metric rule
		else:
			if self.glyph.leftMetricsKey!=None or self.LSB==False:
				self.newL=self.layer.LSB

			if self.glyph.rightMetricsKey!=None or self.RSB==False:
				self.newR=self.layer.RSB

	   #creates glyph with white area polygon
		if len(self.mySelection)<2 and createProofGlyph == True:
			createAreasGlyph(self.font,self.layer,self.layerIndex,poligonos)



	def spaceMain( self, sender ):
		Glyphs.clearLog()
		try:
			#detects if comes from UI
			if dir(sender)[0]=='__class__':
				self.paramArea=int(self.w.area.get())
				self.paramDepth=int(self.w.prof.get())
				self.paramOver=int(self.w.ex.get())
				self.tab=self.w.tab.get()
				self.LSB=self.w.LSB.get()
				self.RSB=self.w.RSB.get()
				self.ancho=float(self.w.ancho.get())


			#self.w.close()

			self.progressBar()

			for layer in self.mySelection:

				if layer.name:
					self.setG(layer)
					self.p.bar.increment(self.wunit)

				#do not execute when
				#DECLARE YOUR EXCEPTIONS HERE
				#no paths
				if not layer.name:
					self.output+='Hay algo raro... Probablemente un salto de linea'
				elif len(layer.paths)<1 and len(layer.components)<1:
				   self.output+='Glyph '+self.glyph.name +" hasn't any path\n"
				#both sidebearings with metric keys
				elif autoAlignment(layer)==False:
					self.output+='Glifo '+self.glyph.name +' has automatic alignment.'+"\n"
				elif self.glyph.leftMetricsKey!=None and self.glyph.rightMetricsKey !=None:
				   self.output+='Glifo '+self.glyph.name +' has metric keys. Dont forget to update it.'+"\n"
				#if it is tabular
				#elif '.tosf' in self.glyph.name or '.tf' in self.glyph.name:
				   #self.output+='Glifo '+self.glyph.name +' se supone tabular..'+"\n"
				#if it is fraction
				elif 'fraction' in self.glyph.name:
				   self.output+='Glifo '+self.glyph.name +': should be checked and done manually.'+"\n"
				#if not...
				else:
					self.setSpace()
					#store values in a list
					self.glyphValues.append([self.layerIndex,self.glyph.name,self.newL,self.newR,self.newWidth])


			self.p.close()

			if window==True and not self.SavePreferences( self ):
				self.output+= "Note: Couldn't save preferences."
			print self.output
			self.output=''

			#set sidebearings in list
			setSidebearings(color,self.font,self.glyphValues)

		#traceback
		except Exception as ex:
			import traceback
			print traceback.format_exc()




htSpacer()
