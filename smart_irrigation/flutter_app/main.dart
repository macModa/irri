import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:geolocator/geolocator.dart';

void main() {
  runApp(SmartIrrigationApp());
}

class SmartIrrigationApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Irrigation',
      theme: ThemeData(
        primarySwatch: Colors.green,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // API Configuration
  final String apiBaseUrl = 'http://192.168.1.100:8000/api';  // Adapter l'IP
  
  // Controllers
  final _plotIdController = TextEditingController();
  final _userNameController = TextEditingController();
  final _areaController = TextEditingController(text: '10.0');
  
  // State
  List<dynamic> plants = [];
  List<dynamic> soilTypes = [];
  String? selectedPlant;
  String? selectedSoilType;
  double? latitude;
  double? longitude;
  bool isLoading = false;
  String? message;
  
  @override
  void initState() {
    super.initState();
    loadPlants();
    loadSoilTypes();
    getCurrentLocation();
  }
  
  // Charger la liste des plantes
  Future<void> loadPlants() async {
    try {
      final response = await http.get(Uri.parse('$apiBaseUrl/plants/'));
      if (response.statusCode == 200) {
        setState(() {
          plants = json.decode(response.body)['results'] ?? json.decode(response.body);
        });
      }
    } catch (e) {
      print('Erreur chargement plantes: $e');
    }
  }
  
  // Charger la liste des types de sol
  Future<void> loadSoilTypes() async {
    try {
      final response = await http.get(Uri.parse('$apiBaseUrl/soil-types/'));
      if (response.statusCode == 200) {
        setState(() {
          soilTypes = json.decode(response.body)['results'] ?? json.decode(response.body);
        });
      }
    } catch (e) {
      print('Erreur chargement types de sol: $e');
    }
  }
  
  // Obtenir la position GPS actuelle
  Future<void> getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          message = 'Service de localisation désactivé';
        });
        return;
      }
      
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            message = 'Permission de localisation refusée';
          });
          return;
        }
      }
      
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high
      );
      
      setState(() {
        latitude = position.latitude;
        longitude = position.longitude;
        message = 'Position GPS obtenue';
      });
    } catch (e) {
      setState(() {
        // Position par défaut (Paris)
        latitude = 48.8566;
        longitude = 2.3522;
        message = 'Position par défaut utilisée';
      });
    }
  }
  
  // Créer une nouvelle parcelle
  Future<void> createPlot() async {
    if (_plotIdController.text.isEmpty || 
        selectedPlant == null || 
        selectedSoilType == null ||
        latitude == null ||
        longitude == null) {
      setState(() {
        message = 'Veuillez remplir tous les champs';
      });
      return;
    }
    
    setState(() {
      isLoading = true;
      message = null;
    });
    
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/plots/'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'plot_id': _plotIdController.text,
          'plant_name': selectedPlant,
          'soil_type_name': selectedSoilType,
          'latitude': latitude,
          'longitude': longitude,
          'area_m2': double.parse(_areaController.text),
          'user_name': _userNameController.text,
        }),
      );
      
      if (response.statusCode == 201) {
        final plotData = json.decode(response.body);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => WateringPlanScreen(
              plotId: _plotIdController.text,
              apiBaseUrl: apiBaseUrl,
            ),
          ),
        );
      } else {
        setState(() {
          message = 'Erreur: ${response.body}';
        });
      }
    } catch (e) {
      setState(() {
        message = 'Erreur de connexion: $e';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Smart Irrigation 🌱'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Titre
            Text(
              'Nouvelle Parcelle',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 20),
            
            // ID Parcelle
            TextField(
              controller: _plotIdController,
              decoration: InputDecoration(
                labelText: 'ID Parcelle *',
                hintText: 'ex: plot_001',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.tag),
              ),
            ),
            SizedBox(height: 16),
            
            // Nom utilisateur
            TextField(
              controller: _userNameController,
              decoration: InputDecoration(
                labelText: 'Votre nom',
                hintText: 'Optionnel',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.person),
              ),
            ),
            SizedBox(height: 16),
            
            // Plante
            DropdownButtonFormField<String>(
              value: selectedPlant,
              decoration: InputDecoration(
                labelText: 'Type de plante *',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.local_florist),
              ),
              items: plants.map<DropdownMenuItem<String>>((plant) {
                return DropdownMenuItem<String>(
                  value: plant['name'],
                  child: Text('${plant['name']} (${plant['water_need']}L/jour)'),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  selectedPlant = value;
                });
              },
            ),
            SizedBox(height: 16),
            
            // Type de sol
            DropdownButtonFormField<String>(
              value: selectedSoilType,
              decoration: InputDecoration(
                labelText: 'Type de sol *',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.landscape),
              ),
              items: soilTypes.map<DropdownMenuItem<String>>((soil) {
                return DropdownMenuItem<String>(
                  value: soil['name'],
                  child: Text(soil['name']),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  selectedSoilType = value;
                });
              },
            ),
            SizedBox(height: 16),
            
            // Surface
            TextField(
              controller: _areaController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Surface (m²)',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.square_foot),
              ),
            ),
            SizedBox(height: 16),
            
            // Position GPS
            Card(
              color: Colors.blue[50],
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Row(
                  children: [
                    Icon(Icons.location_on, color: Colors.blue),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        latitude != null
                            ? 'GPS: ${latitude!.toStringAsFixed(4)}, ${longitude!.toStringAsFixed(4)}'
                            : 'Obtention de la position...',
                        style: TextStyle(fontSize: 12),
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.refresh),
                      onPressed: getCurrentLocation,
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(height: 20),
            
            // Message
            if (message != null)
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: message!.contains('Erreur') ? Colors.red[100] : Colors.green[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(message!, style: TextStyle(fontSize: 14)),
              ),
            SizedBox(height: 20),
            
            // Bouton créer
            ElevatedButton(
              onPressed: isLoading ? null : createPlot,
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              child: isLoading
                  ? CircularProgressIndicator(color: Colors.white)
                  : Text(
                      'Créer et voir le plan d\'arrosage',
                      style: TextStyle(fontSize: 16),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

// Écran d'affichage du plan d'arrosage
class WateringPlanScreen extends StatefulWidget {
  final String plotId;
  final String apiBaseUrl;
  
  WateringPlanScreen({required this.plotId, required this.apiBaseUrl});
  
  @override
  _WateringPlanScreenState createState() => _WateringPlanScreenState();
}

class _WateringPlanScreenState extends State<WateringPlanScreen> {
  Map<String, dynamic>? planData;
  bool isLoading = true;
  String? error;
  
  @override
  void initState() {
    super.initState();
    generatePlan();
  }
  
  Future<void> generatePlan() async {
    setState(() {
      isLoading = true;
      error = null;
    });
    
    try {
      final response = await http.get(
        Uri.parse('${widget.apiBaseUrl}/generate_plan/${widget.plotId}/'),
      );
      
      if (response.statusCode == 200) {
        setState(() {
          planData = json.decode(response.body);
          isLoading = false;
        });
      } else {
        setState(() {
          error = 'Erreur: ${response.statusCode}';
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        error = 'Erreur de connexion: $e';
        isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Plan d\'arrosage'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: generatePlan,
          ),
        ],
      ),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error, size: 64, color: Colors.red),
                      SizedBox(height: 16),
                      Text(error!),
                      SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: generatePlan,
                        child: Text('Réessayer'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // En-tête
                      Card(
                        color: Colors.green[50],
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                planData!['plant_name'] ?? 'Plante',
                                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                              ),
                              SizedBox(height: 8),
                              Text('Parcelle: ${planData!['plot_id']}'),
                              Text('Semaine du: ${planData!['week_start']}'),
                              if (planData!['avg_soil_humidity'] != null)
                                Text('Humidité moyenne: ${planData!['avg_soil_humidity']}%'),
                              Text('Pluie prévue: ${planData!['total_rain_forecast']} mm'),
                            ],
                          ),
                        ),
                      ),
                      SizedBox(height: 20),
                      
                      // Plan hebdomadaire
                      Text(
                        'Plan d\'arrosage',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 12),
                      
                      ...((planData!['plan'] as Map<String, dynamic>).entries.map((entry) {
                        final dayData = entry.value as Map<String, dynamic>;
                        return Card(
                          margin: EdgeInsets.only(bottom: 12),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: Colors.blue,
                              child: Text(
                                entry.key.split('_')[1],
                                style: TextStyle(color: Colors.white),
                              ),
                            ),
                            title: Text(
                              dayData['date'] ?? '',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('💧 Volume: ${dayData['volume_l']} L'),
                                Text('⏱ Durée: ${dayData['duration_min']} min'),
                                Text('🌧 Pluie: ${dayData['rain_forecast_mm']} mm'),
                                Text('🌡 Temp: ${dayData['temp_avg']}°C'),
                              ],
                            ),
                            isThreeLine: true,
                          ),
                        );
                      }).toList()),
                    ],
                  ),
                ),
    );
  }
}
