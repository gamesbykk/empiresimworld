import pygame
import math
import random
import opensimplex
from global_land_mask import globe
from line_profiler import profile
import numpy as np

@profile
def main():
    pygame.init()
    opensimplex.seed(42)  # Seed for reproducibility
    rand=opensimplex.OpenSimplex(random.randint(0,100))  # Random number generator for terrain generation

    # === Config ===
    ROGUES=0
    WIDTH, HEIGHT = 1512, 800
    HEX_RADIUS = 5
    GRID_WIDTH = 160
    GRID_HEIGHT = 80
    BG_COLOR = (20, 20, 20)
    LINE_COLOR = (0, 0, 0)
    FONT_COLOR = (255,255,255)

    import math

    import math

    def pixel_to_latlon(px, py, image_width, image_height):
        """
        Convert pixel coordinates to latitude/longitude in Hobo-Dyer projection.
        
        Args:
            px: Pixel x-coordinate (0 to image_width)
            py: Pixel y-coordinate (0 to image_height)
            image_width: Width of the image in pixels
            image_height: Height of the image in pixels
            
        Returns:
            (latitude, longitude) tuple in degrees
        """
        # Hobo-Dyer projects the whole world from -180 to 180 longitude,
        # and approximately -66.5 to 66.5 latitude
        
        # Normalize pixel coordinates to 0-1 range
        x = px / image_width
        y = py / image_height
        # Convert to projection coordinates (-π to π for x, -1.162 to 1.162 for y)
        lon = (x - 0.5) * 2 * math.pi
        lat = (0.5 - y) * 2 * 1.162
        try:
            # Convert y to latitude (inverse of the projection formula)
            lat = math.degrees(math.asin(lat / 1.162))
        except:
            print(x,y,lon,lat)
        
        # Convert x to longitude
        lon = math.degrees(lon)
        
        return lat, lon


    class Unit:
        def __init__(self, color):
            self.stability = 0.0 
            self.color = color
            self.position = (0, 0)  # Placeholder for position
            self.type='plains'
            self.owner = None
            self.adjacent_units = []

    from sklearn.cluster import DBSCAN
    import numpy as np

    def find_largest_cluster_center(units, radius=1.5):
        # Step 1: Extract positions
        positions = np.array([unit.position for unit in units])
        if len(positions) == 0:
            return None, []
        # Step 2: Run DBSCAN clustering
        db = DBSCAN(eps=radius, min_samples=2).fit(positions)
        labels = db.labels_  # cluster IDs, -1 means noise

        # Step 3: Count cluster sizes
        unique_labels, counts = np.unique(labels[labels != -1], return_counts=True)
        if len(counts) == 0:
            return None, []  # No clusters found

        # Step 4: Get largest cluster label
        largest_cluster_label = unique_labels[np.argmax(counts)]

        # Step 5: Extract units in the largest cluster
        cluster_units = [unit for unit, label in zip(units, labels) if label == largest_cluster_label]
        cluster_positions = np.array([unit.position for unit in cluster_units])

        # Step 6: Compute center of the cluster
        center = tuple(cluster_positions.mean(axis=0))
        center = (round(center[0]), round(center[1]))  # Convert to integer coordinates
        return center, cluster_units

    class Empire:
        def __init__(self, name, color):
            self.name = name
            self.color = color
            self.units = []
            self.resources = 1
            self.forces=1
            self.allies_nonagg=[]
            self.allies_defence=[]
            self.font = pygame.font.SysFont('Arial', round(15*math.sqrt(HEX_RADIUS/10)),True)
            self.text = self.font.render(self.name, True, (255,255,255))  # Darker text for visibility
            self.text_width, self.text_height = self.font.size(self.name)
        def update(self):
            self.resources+=self.resources*sum([u.stability for u in self.units])/100000
            self.forces+=self.forces*sum([u.stability for u in self.units])/100000
        def invade(self, unit):
            unit.color = self.color
            try:
                unit.owner.units.remove(unit) if unit.owner else None  # Remove from previous owner
            except ValueError:
                pass
            unit.owner = self
            self.units.append(unit)
        def show(self,screen):
            
            c,us=find_largest_cluster_center(self.units)
            posus=[u.position for u in us]
            if c and len(us) > 250/HEX_RADIUS:
                px=hex_to_pixel(c[1], c[0], HEX_RADIUS)
                screen.blit(self.text, (px[0]+ WIDTH // 2 - (GRID_WIDTH * HEX_RADIUS * math.sqrt(3)) // 2 - self.text_width//2,px[1]+ HEIGHT // 2 - (GRID_HEIGHT * HEX_RADIUS * 3/2) // 2 - self.text_height//2))
    # Add these at the top
    import numpy as np
    from scipy.ndimage import gaussian_filter

    def create_empire_mask(empire):
        """Generate a smooth mask for an empire's territory"""
        mask = np.zeros((GRID_HEIGHT, GRID_WIDTH))
        
        # Mark all cells belonging to this empire
        for unit in empire.units:
            q, r = unit.position
            mask[q][r] = 1.0
        
        # Apply Gaussian blur for smooth edges
        mask = gaussian_filter(mask, sigma=1.2)  # Adjust sigma for smoother edges
        
        return mask

    def draw_smooth_empires():
        # Create a base texture for the map
        base_texture = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Draw all empires with smooth edges
        for empire in emps:
            mask = create_empire_mask(empire)
            
            for q in range(GRID_HEIGHT):
                for r in range(GRID_WIDTH):
                    if mask[q][r] > 0.01:  # Only draw where influence exists
                        x, y = hex_to_pixel(q, r, HEX_RADIUS)
                        x += WIDTH // 2 - (GRID_WIDTH * HEX_RADIUS * math.sqrt(3)) // 2
                        y += HEIGHT // 2 - (GRID_HEIGHT * HEX_RADIUS * 3/2) // 2
                        
                        # Set color with alpha based on mask strength
                        color = (*empire.color, int(180 * mask[q][r]))  # 180 = max alpha
                        pygame.draw.circle(base_texture, color, (int(x), int(y)), 
                                        int(HEX_RADIUS * (0.8 + 0.4 * mask[q][r])))
        
        screen.blit(base_texture, (0, 0))
    import geopandas as gpd
    from shapely.geometry import Point
    import pandas as pd
    import country_converter as coco
    df=pd.read_csv('Military Expenditure.csv')
    df2=pd.read_csv('world-data-2023.csv')
    df3=pd.read_csv('allies.csv')
    df2=df2.fillna('0')
    # Load country borders (replace with your file path)
    countries = gpd.read_file("ne_110m_admin_0_countries (1)/ne_110m_admin_0_countries.shp")
    #print(countries.crs)
    names=df2['Abbreviation']
    print(names)
    # Filter out tiny countries (optional)
    countries = countries[countries['POP_EST'] > 1_000_000]  # Only countries with >1M population
    print(countries.columns.to_list())
    grid=[[Unit((255,255,255)) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]  # Placeholder for grid data
    emps=[]
    mxpc={df.iloc[i]['Code']:df.iloc[i]['2018'] for i in range(len(df)) if df.iloc[i]['Code'] in countries['ADM0_A3'].values}  # Get country names from the DataFrame
    print(df2['Armed Forces size'].to_list())
    
    m2xpc={names[i]:int(df2.iloc[i]['Armed Forces size'].replace(',','')) for i in range(len(names))} 
    names=[country['NAME'] for idx,country in countries.iterrows()]  # Get country names
    emptocont={}
    print(countries['NAME'].to_list())
    for idx,country in countries.iterrows():
        e=Empire(country['NAME'], (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        try:
            e.resources=mxpc[country['ADM0_A3']]
            e.forces=m2xpc[coco.convert([country['NAME']],to='ISO2')]
            rows=df3.loc[(df3['state_name1']==country['NAME']) | (df3['state_name2']==country['NAME'])]
            if not rows['version4id'].to_list():
                print('Possible error for country: ',country['NAME'])
            e.allies_def=[]
            for idx,row in rows.iterrows():
                if row['state_name2']!=country['NAME'] and row['state_name2'] in countries['NAME'].to_list():
                    if row['defense']:
                        e.allies_def.append(row['state_name2'])
                    if row['nonaggression']:
                        e.allies_nonagg.append(row['state_name2'])
                elif row['state_name1']!=country['NAME'] and row['state_name1'] in countries['NAME'].to_list():
                    if row['defense']:
                        e.allies_def.append(row['state_name1'])
                    if row['nonaggression']:
                        e.allies_nonagg.append(row['state_name1'])
            
        except KeyError:

            countries.drop(idx, inplace=True)  # Remove country if not found in DataFrame
            print(f"Country {country['NAME']} not found in DataFrame, skipping.")
            continue  # Skip if country code not found in DataFrame
        emptocont[country['NAME']]= e


    emps.extend(emptocont.values())  # Add all empires to the list
    for i in range(len(emps)):
        idx=0
        rems=[]
        for e in emps[i].allies_defence:
            if e not in countries['NAME'].to_list():
                rems.append(idx)
        for e in emps[i].allies_nonagg:
            if e not in countries['NAME'].to_list():
                rems.append(idx)
            idx+=1
        emps[i].allies_defence=[emps[i].allies_defence[xx] for xx in range(len(emps[i].allies_defence)) if xx not in rems]
        emps[i].allies_nonagg=[emps[i].allies_nonagg[xx] for xx in range(len(emps[i].allies_nonagg)) if xx not in rems]
    for r in range(GRID_HEIGHT):
        for q in range(GRID_WIDTH):
            lat,lon = pixel_to_latlon(q,r, GRID_WIDTH, GRID_HEIGHT)  # Convert pixel to lat/lon
            is_land=globe.is_land(lat, lon)  # Check if the position is land
            grid[r][q].position = (r, q)  # Set position for each unit
            point = Point(lon, lat)
            point_geo = gpd.GeoSeries(point, crs=countries.crs)
            country = countries[countries.geometry.contains(point_geo.geometry.squeeze())]
            if not is_land:
                grid[r][q].color = (0, 0, 255)
                grid[r][q].type = 'water'
            elif False:
                grid[r][q].color = (145, 118, 76)
                grid[r][q].type = 'mountains'
            else:
        
                grid[r][q].color = (0, 255, 0)
                grid[r][q].type = 'plains'
                if not country.empty:
                    country_name = country.iloc[0]['NAME']
                    grid[r][q].owner = emptocont[country_name]
                    grid[r][q].owner.invade(grid[r][q])
                    grid[r][q].stability = 1.0
                #if random.random() < 0.05:
                    #print(f"Creating new empire at {q}, {r}")
                    #emp = Empire(random.choice(empire_names), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                    #emps.append(emp)
                    #emp.invade(grid[q][r])
                    #grid[q][r].stability = 1.0  # Set initial stability for the unit
            grid[r][q].neighboring_units = [grid[(r + dr)][(q + dq)%GRID_WIDTH] for dq in [-1, 0, 1] for dr in [-1, 0, 1] if (dq != 0 or dr != 0) and 0 <= r + dr < GRID_HEIGHT]



    empire_names = [
        "The Aurion Dominion", "The Vexis Imperium", "The Dravon Supremacy", 
        "The Zorathian Hegemony", "The Sylthari Expanse", "The Nyxian Sovereignty", 
        "The Obsidian Throne", "The Celvaxian Accord", "The Krythos Federation", 
        "The Umbral Ascendancy", "The Tarethian Star Collective", "The Vorlux Dominion", 
        "The Xypharion Empire", "The Quorvian Enclave", "The Yldari Concord", 
        "The Raxxian Imperium", "The Zenithian Hierarchy", "The Oryxian Dominion", 
        "The Vhaldrian Sovereignty", "The Pyraxian Coalition", "The Eclipsion Dynasty", 
        "The Thalassian Dominion", "The Vorthan League", "The Myrthari Empire", 
        "The Zypharion Dominion", "The Xandros Imperium", "The Qelthari Federation", 
        "The Duskborn Hegemony", "The Solvaxian Mandate", "The Veythari Ascendancy", 
        "The Kaldorian Star Empire", "The Nyrvanian Sovereignty", "The Ixthari Dominion", 
        "The Zorvian Pact", "The Eldrosian Imperium", "The Vexarion Dominion", 
        "The Sythari Concord", "The Orphion Hegemony", "The Xyrthos Federation", 
        "The Dralkian Supremacy", "The Ythari Dominion", "The Vexorian Dynasty", 
        "The Zenthari Empire", "The Qorvian Sovereignty", "The Kylthari Ascendancy", 
        "The Xandarian Dominion", "The Vorthax Imperium", "The Myxarion Federation", 
        "The Sylthos Hegemony", "The Dravaxian Mandate", "The Zorvian Star Empire", 
        "The Elythari Dominion", "The Vexthari Sovereignty", "The Krythian Pact", 
        "The Nyxarion Imperium", "The Qylthari Dominion", "The Xyrtharian Federation", 
        "The Duskari Hegemony", "The Solthos Ascendancy", "The Veythos Dynasty", 
        "The Kaldarion Star Empire", "The Nyrthari Sovereignty", "The Ixthos Dominion", 
        "The Zoraxian Pact", "The Eldrith Imperium", "The Vexthos Dominion", 
        "The Sypharion Concord", "The Orphax Hegemony", "The Xyrthian Federation", 
        "The Dralkari Supremacy", "The Ythos Dominion", "The Vextharian Dynasty", 
        "The Zenthos Empire", "The Qorvax Sovereignty", "The Kylthos Ascendancy", 
        "The Xandros Dominion", "The Vorthaxian Imperium", "The Myxthari Federation", 
        "The Sylthax Hegemony", "The Dravos Mandate", "The Zorax Star Empire", 
        "The Elythos Dominion", "The Vexthos Sovereignty", "The Krythax Pact", 
        "The Nyxthari Imperium", "The Qylthos Dominion", "The Xyrthax Federation", 
        "The Duskthari Hegemony", "The Solthax Ascendancy", "The Veythos Dynasty", 
        "The Kaldax Star Empire", "The Nyrthos Sovereignty", "The Ixthax Dominion", 
        "The Zorvax Pact", "The Eldrax Imperium", "The Vexthax Dominion", 
        "The Syphax Concord", "The Orphaxian Hegemony", "The Xyrthaxian Federation", 
        "The Dralkax Supremacy", "The Ythax Dominion", "The Vexthaxian Dynasty", 
        "The Zenthax Empire", "The Qorvaxian Sovereignty", "The Kylthax Ascendancy", 
        "The Xandax Dominion", "The Vorthaxian Imperium", "The Myxthax Federation", 
        "The Sylthaxian Hegemony", "The Dravax Mandate", "The Zoraxian Star Empire", 
        "The Elythax Dominion", "The Vexthaxian Sovereignty", "The Krythaxian Pact", 
        "The Nyxthax Imperium", "The Qylthax Dominion", "The Xyrthaxian Federation", 
        "The Duskthax Hegemony", "The Solthaxian Ascendancy", "The Veythax Dynasty", 
        "The Kaldaxian Star Empire", "The Nyrthax Sovereignty", "The Ixthaxian Dominion", 
        "The Zorvaxian Pact", "The Eldraxian Imperium", "The Vexthaxian Dominion", 
        "The Syphaxian Concord", "The Orphaxian Hegemony", "The Xyrthaxian Federation", 
        "The Dralkaxian Supremacy", "The Ythaxian Dominion", "The Vexthaxian Dynasty", 
        "The Zenthaxian Empire", "The Qorvaxian Sovereignty", "The Kylthaxian Ascendancy", 
        "The Xandaxian Dominion", "The Vorthaxian Imperium", "The Myxthaxian Federation", 
        "The Sylthaxian Hegemony", "The Dravaxian Mandate", "The Zoraxian Star Empire", 
        "The Elythaxian Dominion", "The Vexthaxian Sovereignty", "The Krythaxian Pact", 
        "The Nyxthaxian Imperium", "The Qylthaxian Dominion", "The Xyrthaxian Federation"
    ]
    # === Config ===
    VISUAL_WIDTH, VISUAL_HEIGHT = 320, 160  # 4x detail of 40x40
    GAME_WIDTH, GAME_HEIGHT = 160, 80

    # Generate a detailed visual map
    visual_grid = [[(0,0,0) for _ in range(VISUAL_HEIGHT)] for _ in range(VISUAL_WIDTH)]

    for q in range(VISUAL_WIDTH):
        for r in range(VISUAL_HEIGHT):
            try:
                lat, lon = pixel_to_latlon(q,r, VISUAL_WIDTH, VISUAL_HEIGHT)
                if globe.is_land(lat, lon):
                    # Add noise-based detail
                    detail = int(opensimplex.noise2(q/20, r/20) * 30)
                    visual_grid[q][r] = (100+detail, 150+detail, 70+detail)
                else:
                    depth = int(opensimplex.noise2(q/15, r/15) * 50)
                    visual_grid[q][r] = (0, 50+depth, 100+depth)
            except Exception as e:
                pass
                #visual_grid[q][r] = (0, 0, 0)
    player_empire = random.choice(emps)
    emps.remove(player_empire)  # Remove player empire from the list
    player_empire
    rogue=Empire("Rogue Unit", (255, 0, 0))
    # === Init ===
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Hex Grid")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 10)
    show_stability = False  # Toggle for stability display

    # === Hex Math ===
    def hex_to_pixel(q, r, radius):
        """Convert axial hex coordinates (q, r) to pixel coordinates."""
        x = radius * math.sqrt(3) * (q+(r%2)/2)
        y = radius * 3/2 * r + radius
        return x, y

    def hex_corner(center, radius, i):
        """Get the i-th corner of a hexagon."""
        angle_deg = 60 * i - 30  # Pointy-top
        angle_rad = math.radians(angle_deg)
        x = center[0] + radius * math.cos(angle_rad)
        y = center[1] + radius * math.sin(angle_rad)
        return x, y

    def draw_hex(center, radius, color, border_color=None):
        points = [hex_corner(center, radius, i) for i in range(6)]
        pygame.draw.polygon(screen, color, points)
        #if border_color:
            #pygame.draw.polygon(screen, border_color, points, width=1)
    x_off=WIDTH//2 - (GAME_WIDTH * HEX_RADIUS * math.sqrt(3))//2
    y_off=HEIGHT//2 - (GAME_HEIGHT * HEX_RADIUS * 3/2)//2
    hex_centers = []
    for r in range(GAME_HEIGHT):
        row_centers = []
        for q in range(GAME_WIDTH):
            game_x, game_y = hex_to_pixel(q, r, HEX_RADIUS)
            game_x += x_off
            game_y += y_off
            row_centers.append((game_x, game_y))
        hex_centers.append(row_centers)
    hex_scale_h = VISUAL_HEIGHT / (GAME_HEIGHT)  # How many visual pixels per game hex
    hex_scale_w = VISUAL_WIDTH / (GAME_WIDTH)  # How many visual pixels per game hex
    hex_radius_2 = HEX_RADIUS * 2
    inv_hex_scale_h = 1.0 / hex_scale_h
    inv_hex_scale_w = 1.0 / hex_scale_w
    x_off=WIDTH//2 - (GAME_WIDTH * HEX_RADIUS * math.sqrt(3))//2
    y_off=HEIGHT//2 - (GAME_HEIGHT * HEX_RADIUS * 3/2)//2
    vq_coords = np.arange(0, VISUAL_WIDTH)
    vr_coords = np.arange(0, VISUAL_HEIGHT)
    vq_grid, vr_grid = np.meshgrid(vq_coords, vr_coords)
    game_x=np.array([[hex_to_pixel(int(c//hex_scale_h),int(r//hex_scale_w), HEX_RADIUS)[0]+x_off for c in range(len(hex_centers[int(r//hex_scale_h)])*int(hex_scale_w))]for r in range(len(hex_centers)*int(hex_scale_h))])
    game_y=np.array([[hex_to_pixel(int(c//hex_scale_h),int(r//hex_scale_w), HEX_RADIUS)[1]+y_off for c in range(len(hex_centers[int(r//hex_scale_h)])*int(hex_scale_w))]for r in range(len(hex_centers)*int(hex_scale_h))])
    gx=np.array([[0,1]*(VISUAL_WIDTH//2) for _ in range(VISUAL_HEIGHT)])
    gy=np.array([[r%2]*VISUAL_WIDTH for r in range(VISUAL_HEIGHT)])

    # Vectorized pixel position calculation
    px_x = game_x + (gx) * inv_hex_scale_h * hex_radius_2
    px_y = game_y + (gy) * inv_hex_scale_w * hex_radius_2
    # === Draw Grid ===
    def draw_hex_grid():
        hex_scale_h = VISUAL_HEIGHT / (GAME_HEIGHT)  # How many visual pixels per game hex
        hex_scale_w = VISUAL_WIDTH / (GAME_WIDTH)  # How many visual pixels per game hex
        hex_scale_h_int = int(hex_scale_h)
        hex_scale_w_int = int(hex_scale_w)
        for r in range(GAME_HEIGHT):
            for q in range(GAME_WIDTH ):
                # Game position
                #if game_x>WIDTH//2:
                    #print(game_x)
                g=grid[r][q]
                # Calculate bounds once per hex
                vq_start = max(0, q * hex_scale_h_int)
                vq_end = min(VISUAL_WIDTH, (q + 1) * hex_scale_h_int)
                vr_start = max(0, r * hex_scale_w_int)
                vr_end = min(VISUAL_HEIGHT,(r + 1) * hex_scale_w_int)
                
                # Draw detailed background
                for vq in range(vq_start, vq_end):
                    for vr in range(vr_start, vr_end):
                        
                        #if 0 <= vq < VISUAL_WIDTH and 0 <= vr < VISUAL_HEIGHT:
                        col= visual_grid[vq][vr]
                        if visual_grid[vq][vr][0]>0:
                            if g.owner:
                                col = g.color
                        pygame.draw.circle(screen, col, (int(px_x[vr][vq]), int(px_y[vr][vq])), 1)
                
                # Draw empire overlay (original hexes)
                #if grid[q][r].owner:
                    #draw_hex((game_x, game_y), HEX_RADIUS, (*grid[q][r].color, 150))  # Semi-transparent
    # === Main Loop ===
    running = True
    while running:
        clock.tick(60)
        screen.fill(BG_COLOR)
        
        for r in range(GRID_HEIGHT):
            for q in range(GRID_WIDTH):
                unit = grid[r][q]
                self_neighbors = [neighbor for neighbor in unit.neighboring_units if neighbor.owner == unit.owner]
                for u in self_neighbors:
                    u.stability += 0.005*unit.stability/len(self_neighbors)
                if self_neighbors:
                    unit.stability=unit.stability*0.99
                if unit.stability > 1.0:
                    unit.stability = 1.0
                elif unit.stability < 0.0:
                    unit.stability = 0.0

                if unit.owner:
                    if random.random() < 0.01:  # Randomly invade
                        foreign_neighors = [neighbor for neighbor in unit.neighboring_units if neighbor.owner != unit.owner and neighbor.owner != rogue and neighbor.type != 'water' and ((not neighbor.owner) or (neighbor.owner.name not in unit.owner.allies_nonagg))]
                        if foreign_neighors:
                            
                            target_unit = random.choice(foreign_neighors)
                            un_e_stability = sum([u.stability for u in unit.owner.units])
                            target_unit_stability = sum([u.stability for u in target_unit.owner.units]) if target_unit.owner else 0
                            unit_resources=unit.owner.resources+0.01*sum([emptocont[empp].resources for empp in unit.owner.allies_defence])
                            unit_forces=unit.owner.forces+0.01*sum([emptocont[empp].forces for empp in unit.owner.allies_defence])
                            if target_unit.owner:
                                target_resources=target_unit.owner.resources+0.01*sum([emptocont[empp].resources for empp in target_unit.owner.allies_defence])
                                target_forces=unit.owner.forces+0.01*sum([emptocont[empp].forces for empp in target_unit.owner.allies_defence])
                                if unit_resources*unit.stability*un_e_stability*unit_forces>target_forces*target_resources*target_unit_stability*target_unit.stability*(1.5-0.5*int(target_unit.type!='mountains')+10**100*int(target_unit.type=='water')):
                                    unit.owner.resources-=unit.owner.resources*unit.stability*un_e_stability/len(unit.owner.units)*0.1
                                    target_unit.owner.resources-=unit.owner.resources*unit.stability*un_e_stability/len(unit.owner.units)*0.1
                                    if target_unit.owner.resources<0:
                                        target_unit.owner.resources=0
                                    unit.owner.forces-=unit.owner.forces*unit.stability*un_e_stability/len(unit.owner.units)*0.1
                                    target_unit.owner.forces-=target_unit.owner.forces*target_unit.stability*target_unit_stability/len(target_unit.owner.units)*0.1
                                    unit.stability += 0.5

                                    target_unit.stability += 0.5
                                    unit.owner.invade(target_unit)
                            else:
                                unit.stability += 0.5

                                target_unit.stability += 0.5
                                unit.owner.invade(target_unit)
                    elif unit.stability<0.1 and random.random() < 0.0005 and ROGUES:  # Rogue unit invasion
                        self_neighbors = [neighbor for neighbor in unit.neighboring_units if neighbor.owner == unit.owner]
                        r_ex=0
                        r_emp=None
                        for emp in emps:
                            if emp.name[-7:]=='(ROGUE)':
                                r_ex=1
                                r_emp=emp
                        if not r_ex:
                            rogue = Empire(f'{unit.owner.name}(ROGUE)', (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                            emps.append(rogue)
                        else:
                            rogue=r_emp
                        
                        rogue.invade(unit)
                        if self_neighbors:
                            target_unit = random.choice(self_neighbors)
                            if random.random() < 0.5:
                                unit.stability+=0.5

                                target_unit.stability += 0.5
                                
                                rogue.invade(target_unit)
                if unit.stability > 1.0:
                    unit.stability = 1.0
                elif unit.stability < 0.0:
                    unit.stability = 0.0

        draw_hex_grid()
        for emp in emps:
            emp.update()
            emp.show(screen)  # Display empire names
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    show_stability = not show_stability  # Toggle stability display

    pygame.quit()
if __name__=='__main__':
    main()
