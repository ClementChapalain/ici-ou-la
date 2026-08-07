fetch("FR_dep.svg")
  .then(response => response.text())
  .then(svg => {
    document.querySelector("#map-container").innerHTML = svg;

    initMap();
  });

function initMap() {

  const tooltip = document.querySelector("#tooltip");

window.departements = {
  "dep_01": { nom: "Ain", region: "Auvergne-Rhône-Alpes" },
  "dep_02": { nom: "Aisne", region: "Hauts-de-France" },
  "dep_2A": { nom: "Corse-du-Sud", region: "Corse" },
  "dep_2B": { nom: "Haute-Corse", region: "Corse" },
  "dep_03": { nom: "Allier", region: "Auvergne-Rhône-Alpes" },
  "dep_04": { nom: "Alpes-de-Haute-Provence", region: "Provence-Alpes-Côte d'Azur" },
  "dep_05": { nom: "Hautes-Alpes", region: "Provence-Alpes-Côte d'Azur" },
  "dep_06": { nom: "Alpes-Maritimes", region: "Provence-Alpes-Côte d'Azur" },
  "dep_07": { nom: "Ardèche", region: "Auvergne-Rhône-Alpes" },
  "dep_08": { nom: "Ardennes", region: "Grand Est" },
  "dep_09": { nom: "Ariège", region: "Occitanie" },
  "dep_10": { nom: "Aube", region: "Grand Est" },
  "dep_11": { nom: "Aude", region: "Occitanie" },
  "dep_12": { nom: "Aveyron", region: "Occitanie" },
  "dep_13": { nom: "Bouches-du-Rhône", region: "Provence-Alpes-Côte d'Azur" },
  "dep_14": { nom: "Calvados", region: "Normandie" },
  "dep_15": { nom: "Cantal", region: "Auvergne-Rhône-Alpes" },
  "dep_16": { nom: "Charente", region: "Nouvelle-Aquitaine" },
  "dep_17": { nom: "Charente-Maritime", region: "Nouvelle-Aquitaine" },
  "dep_18": { nom: "Cher", region: "Centre-Val de Loire" },
  "dep_19": { nom: "Corrèze", region: "Nouvelle-Aquitaine" },
  "dep_2A": { nom: "Corse-du-Sud", region: "Corse" },
  "dep_2B": { nom: "Haute-Corse", region: "Corse" },
  "dep_21": { nom: "Côte-d'Or", region: "Bourgogne-Franche-Comté" },
  "dep_22": { nom: "Côtes-d'Armor", region: "Bretagne" },
  "dep_23": { nom: "Creuse", region: "Nouvelle-Aquitaine" },
  "dep_24": { nom: "Dordogne", region: "Nouvelle-Aquitaine" },
  "dep_25": { nom: "Doubs", region: "Bourgogne-Franche-Comté" },
  "dep_26": { nom: "Drôme", region: "Auvergne-Rhône-Alpes" },
  "dep_27": { nom: "Eure", region: "Normandie" },
  "dep_28": { nom: "Eure-et-Loir", region: "Centre-Val de Loire" },
  "dep_29": { nom: "Finistère", region: "Bretagne" },
  "dep_30": { nom: "Gard", region: "Occitanie" },
  "dep_31": { nom: "Haute-Garonne", region: "Occitanie" },
  "dep_32": { nom: "Gers", region: "Occitanie" },
  "dep_33": { nom: "Gironde", region: "Nouvelle-Aquitaine" },
  "dep_34": { nom: "Hérault", region: "Occitanie" },
  "dep_35": { nom: "Ille-et-Vilaine", region: "Bretagne" },
  "dep_36": { nom: "Indre", region: "Centre-Val de Loire" },
  "dep_37": { nom: "Indre-et-Loire", region: "Centre-Val de Loire" },
  "dep_38": { nom: "Isère", region: "Auvergne-Rhône-Alpes" },
  "dep_39": { nom: "Jura", region: "Bourgogne-Franche-Comté" },
  "dep_40": { nom: "Landes", region: "Nouvelle-Aquitaine" },
  "dep_41": { nom: "Loir-et-Cher", region: "Centre-Val de Loire" },
  "dep_42": { nom: "Loire", region: "Auvergne-Rhône-Alpes" },
  "dep_43": { nom: "Haute-Loire", region: "Auvergne-Rhône-Alpes" },
  "dep_44": { nom: "Loire-Atlantique", region: "Pays de la Loire" },
  "dep_45": { nom: "Loiret", region: "Centre-Val de Loire" },
  "dep_46": { nom: "Lot", region: "Occitanie" },
  "dep_47": { nom: "Lot-et-Garonne", region: "Nouvelle-Aquitaine" },
  "dep_48": { nom: "Lozère", region: "Occitanie" },
  "dep_49": { nom: "Maine-et-Loire", region: "Pays de la Loire" },
  "dep_50": { nom: "Manche", region: "Normandie" },
  "dep_51": { nom: "Marne", region: "Grand Est" },
  "dep_52": { nom: "Haute-Marne", region: "Grand Est" },
  "dep_53": { nom: "Mayenne", region: "Pays de la Loire" },
  "dep_54": { nom: "Meurthe-et-Moselle", region: "Grand Est" },
  "dep_55": { nom: "Meuse", region: "Grand Est" },
  "dep_56": { nom: "Morbihan", region: "Bretagne" },
  "dep_57": { nom: "Moselle", region: "Grand Est" },
  "dep_58": { nom: "Nièvre", region: "Bourgogne-Franche-Comté" },
  "dep_59": { nom: "Nord", region: "Hauts-de-France" },
  "dep_60": { nom: "Oise", region: "Hauts-de-France" },
  "dep_61": { nom: "Orne", region: "Normandie" },
  "dep_62": { nom: "Pas-de-Calais", region: "Hauts-de-France" },
  "dep_63": { nom: "Puy-de-Dôme", region: "Auvergne-Rhône-Alpes" },
  "dep_64": { nom: "Pyrénées-Atlantiques", region: "Nouvelle-Aquitaine" },
  "dep_65": { nom: "Hautes-Pyrénées", region: "Occitanie" },
  "dep_66": { nom: "Pyrénées-Orientales", region: "Occitanie" },
  "dep_67": { nom: "Bas-Rhin", region: "Grand Est" },
  "dep_68": { nom: "Haut-Rhin", region: "Grand Est" },
  "dep_69": { nom: "Rhône", region: "Auvergne-Rhône-Alpes" },
  "dep_70": { nom: "Haute-Saône", region: "Bourgogne-Franche-Comté" },
  "dep_71": { nom: "Saône-et-Loire", region: "Bourgogne-Franche-Comté" },
  "dep_72": { nom: "Sarthe", region: "Pays de la Loire" },
  "dep_73": { nom: "Savoie", region: "Auvergne-Rhône-Alpes" },
  "dep_74": { nom: "Haute-Savoie", region: "Auvergne-Rhône-Alpes" },
  "dep_75": { nom: "Paris", region: "Île-de-France" },
  "dep_76": { nom: "Seine-Maritime", region: "Normandie" },
  "dep_77": { nom: "Seine-et-Marne", region: "Île-de-France" },
  "dep_78": { nom: "Yvelines", region: "Île-de-France" },
  "dep_79": { nom: "Deux-Sèvres", region: "Nouvelle-Aquitaine" },
  "dep_80": { nom: "Somme", region: "Hauts-de-France" },
  "dep_81": { nom: "Tarn", region: "Occitanie" },
  "dep_82": { nom: "Tarn-et-Garonne", region: "Occitanie" },
  "dep_83": { nom: "Var", region: "Provence-Alpes-Côte d'Azur" },
  "dep_84": { nom: "Vaucluse", region: "Provence-Alpes-Côte d'Azur" },
  "dep_85": { nom: "Vendée", region: "Pays de la Loire" },
  "dep_86": { nom: "Vienne", region: "Nouvelle-Aquitaine" },
  "dep_87": { nom: "Haute-Vienne", region: "Nouvelle-Aquitaine" },
  "dep_88": { nom: "Vosges", region: "Grand Est" },
  "dep_89": { nom: "Yonne", region: "Bourgogne-Franche-Comté" },
  "dep_90": { nom: "Territoire de Belfort", region: "Bourgogne-Franche-Comté" },
  "dep_91": { nom: "Essonne", region: "Île-de-France" },
  "dep_92": { nom: "Hauts-de-Seine", region: "Île-de-France" },
  "dep_93": { nom: "Seine-Saint-Denis", region: "Île-de-France" },
  "dep_94": { nom: "Val-de-Marne", region: "Île-de-France" },
  "dep_95": { nom: "Val-d'Oise", region: "Île-de-France" }
};

  document.querySelectorAll("#map-container path").forEach(dep => {

    dep.addEventListener("mouseenter", (e) => {
      tooltip.textContent = departements[dep.id].nom + " (" + dep.id.slice(dep.id.length-2) + ")";
      tooltip.style.display = "block";
    });

    dep.addEventListener("mousemove", (e) => {
      tooltip.style.left = e.clientX + 15 + "px";
      tooltip.style.top = e.clientY + 15 + "px";
    });

    dep.addEventListener("mouseleave", () => {
      tooltip.style.display = "none";
    });

    dep.addEventListener("click", () => {
      departementClique(dep.id);
  });

  });

}

function surlignerDepartement(code, classe) {
  document
    .getElementById(code)
    ?.classList.add(classe);
}

function colorerDepartement(code, classe) {
  const departement = document.getElementById(code);
  if (departement) {
    departement.classList.add(classe);
  }
}