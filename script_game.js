let parties = [];
let partieActuelle;
let articleActuel = 0;
let score = 0;
let carte;
let marqueurChoix;
let marqueurReponse;
let ligneDistance;
let etiquetteDistance;
let reponseEnCours = false;
let viseur;

const SCORE_MAXIMUM = 5_000;
const DISTANCE_MAXIMUM_KM = 600;
const cacheLieux = new Map();

initialiserCarte();

Papa.parse("articles.csv", {
  download: true,
  header: true,
  skipEmptyLines: true,
  complete(results) {
    parties = results.data.filter(ligne => ligne.Date);
    demarrerPartie();
  },
  error() {
    afficherErreur("Les questions n'ont pas pu être chargées.");
  }
});

function initialiserCarte() {
  carte = L.map("map-container", { minZoom: 5, maxZoom: 16 }).setView([46.6, 2.4], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png", {
    attribution: "Données © OpenStreetMap contributors — rendu © OpenStreetMap France",
    subdomains: "abc",
    maxZoom: 20
  }).addTo(carte);

  carte.on("click", evenement => {
    if (reponseEnCours) {
      articleSuivant();
    } else {
      jouer(evenement.latlng);
    }
  });
  ajouterViseur();
}

function ajouterViseur() {
  viseur = document.createElement("div");
  viseur.className = "guess-cursor";
  viseur.setAttribute("aria-hidden", "true");
  carte.getContainer().appendChild(viseur);

  carte.on("mousemove", evenement => {
    viseur.style.left = `${evenement.containerPoint.x}px`;
    viseur.style.top = `${evenement.containerPoint.y}px`;
    viseur.style.display = reponseEnCours ? "none" : "block";
  });
  carte.on("mouseout", () => {
    viseur.style.display = "none";
  });
}

function transformerLigne(ligne) {
  return {
    date: ligne.Date,
    articles: [1, 2, 3, 4, 5].map(numero => creerArticle(ligne, numero))
  };
}

function creerArticle(ligne, numero) {
  return {
    titreOriginal: ligne[`${numero}-Titre_original`],
    titreTronque: ligne[`${numero}-Titre_tronqué`],
    type: ligne[`${numero}-Type`],
    lieu: ligne[`${numero}-Lieu`],
    lien: ligne[`${numero}-Lien`],
    latitude: Number.parseFloat(ligne[`${numero}-Latitude`]),
    longitude: Number.parseFloat(ligne[`${numero}-Longitude`]),
    position: null
  };
}

async function demarrerPartie() {
  partieActuelle = transformerLigne(choisirPartie());
  articleActuel = 0;
  score = 0;
  await afficherArticle();
}

function choisirPartie() {
  const dateDemandee = new URLSearchParams(window.location.search).get("date");
  if (dateDemandee) {
    const [annee, mois, jour] = dateDemandee.split("-").map(Number);
    const cle = `${jour}/${mois}/${annee}`;
    const ligne = parties.find(ligne => ligne.Date === cle);
    if (ligne) return ligne;
  }
  return parties[0];
}

async function afficherArticle() {
  const article = partieActuelle.articles[articleActuel];
  const feedback = document.querySelector("#feedback");

  reponseEnCours = false;
  document.querySelector("#map-container").classList.remove("map--ready");
  supprimerMarqueurs();
  document.querySelector(".article").textContent = article.titreTronque;
  document.querySelector(".article-link").textContent = "";
  document.querySelector("#numero").textContent = articleActuel + 1;
  document.querySelector("#next-button").style.display = "none";
  feedback.textContent = "Positionnement du lieu sur la carte…";

  try {
    article.position = await geolocaliser(article);
    feedback.textContent = "Cliquez sur la carte pour placer votre réponse.";
  } catch (erreur) {
    afficherErreur(`Le lieu « ${article.lieu} » n'a pas pu être localisé. Passez à la question suivante.`);
    afficherBoutonSuivant();
  }
}

async function geolocaliser(article) {
  const lieu = article.lieu;
  if (cacheLieux.has(lieu)) return cacheLieux.get(lieu);

  if (Number.isFinite(article.latitude) && Number.isFinite(article.longitude)) {
    const position = L.latLng(article.latitude, article.longitude);
    cacheLieux.set(lieu, position);
    return position;
  }

  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.search = new URLSearchParams({
    q: `${lieu}, France`,
    format: "jsonv2",
    limit: "1",
    countrycodes: "fr"
  });

  const reponse = await fetch(url, { headers: { Accept: "application/json" } });
  if (!reponse.ok) throw new Error("géocodage indisponible");

  const resultats = await reponse.json();
  if (!resultats.length) throw new Error("lieu introuvable");

  const position = L.latLng(Number(resultats[0].lat), Number(resultats[0].lon));
  cacheLieux.set(lieu, position);
  return position;
}

function jouer(positionJoueur) {
  const article = partieActuelle.articles[articleActuel];
  if (reponseEnCours || !article.position) return;

  reponseEnCours = true;
  document.querySelector("#map-container").classList.add("map--ready");
  document.querySelector(".article").textContent = article.titreOriginal;

  marqueurChoix = creerMarqueur(positionJoueur, "#001bcc", "Votre réponse");
  marqueurReponse = creerMarqueur(article.position, "#2e9c5b", `Le lieu : ${article.lieu}`);

  const distanceKm = carte.distance(positionJoueur, article.position) / 1000;
  const points = calculerPoints(distanceKm);
  score += points;

  afficherLiaison(positionJoueur, article.position, distanceKm, points);
  afficherResultat(distanceKm, points, article.lieu);
  document.querySelector(".article-link").innerHTML =
    `<a href="${article.lien}" target="_blank" rel="noreferrer">Lire l'article<span aria-hidden="true"> ↗</span></a>`;
  afficherBoutonSuivant();
}

function creerMarqueur(position, couleur, titre) {
  return L.circleMarker(position, {
    radius: 10,
    color: "#ffffff",
    weight: 3,
    fillColor: couleur,
    fillOpacity: 1
  }).addTo(carte).bindTooltip(titre, { direction: "top", offset: [0, -10] });
}

function afficherLiaison(depart, arrivee, distanceKm, points) {
  ligneDistance = L.polyline([depart, arrivee], {
    color: "#001bcc",
    weight: 3,
    dashArray: "8 8",
    opacity: 0.8
  }).addTo(carte);

  const milieu = L.latLng(
    (depart.lat + arrivee.lat) / 2,
    (depart.lng + arrivee.lng) / 2
  );
  etiquetteDistance = L.tooltip({
    permanent: true,
    direction: "center",
    className: "distance-label"
  })
    .setLatLng(milieu)
    .setContent(`${Math.round(distanceKm).toLocaleString("fr-FR")} km · ${points.toLocaleString("fr-FR")} pts`)
    .addTo(carte);
}

function calculerPoints(distanceKm) {
  const distanceNormalisee = Math.min(distanceKm / DISTANCE_MAXIMUM_KM, 1);
  return Math.round(SCORE_MAXIMUM * (1 - distanceNormalisee) ** 2);
}

function afficherResultat(distanceKm, points, lieu) {
  const distance = Math.round(distanceKm).toLocaleString("fr-FR");
  const scoreFormate = points.toLocaleString("fr-FR");
  document.querySelector("#feedback").innerHTML =
    `📍 <strong>${lieu}</strong> était à <strong>${distance} km</strong> de votre réponse.<br>` +
    `Vous gagnez <strong>${scoreFormate} points</strong>.`;
}

function afficherBoutonSuivant() {
  const bouton = document.querySelector("#next-button");
  bouton.textContent = articleActuel === 4 ? "Voir mon score" : "Lieu suivant";
  bouton.style.display = "block";
  bouton.onclick = articleSuivant;
}

async function articleSuivant() {
  articleActuel += 1;
  if (articleActuel < 5) {
    await afficherArticle();
  } else {
    finPartie();
  }
}

function supprimerMarqueurs() {
  [marqueurChoix, marqueurReponse, ligneDistance, etiquetteDistance].forEach(calque => {
    if (calque) carte.removeLayer(calque);
  });
  marqueurChoix = null;
  marqueurReponse = null;
  ligneDistance = null;
  etiquetteDistance = null;
}

function afficherErreur(message) {
  document.querySelector("#feedback").textContent = message;
}

function finPartie() {
  document.querySelector(".game").classList.add("game--finished");
  document.querySelector(".article").style.display = "none";
  document.querySelector(".question-card").style.display = "none";
  document.querySelector("#map-container").style.display = "none";
  document.querySelector("#feedback").style.display = "none";
  document.querySelector("#next-button").style.display = "none";
  document.querySelector(".game-meta").style.display = "none";
  document.querySelector("#end-screen").style.display = "block";
  document.querySelector("#final-score").textContent = score.toLocaleString("fr-FR");
  document.querySelector("#share-button").onclick = ouvrirPartage;
  marquerPartieJouee();

  const palier = messageSelonScore(score);
  document.querySelector("#end-title").textContent = palier.titre;
  document.querySelector("#end-message").textContent = palier.message;
  afficherRecap();
}

function marquerPartieJouee() {
  const [jour, mois, annee] = partieActuelle.date.split("/");
  const iso = `${annee}-${mois}-${jour}`;
  const CLEF_PARTIES_JOUÉES = "icioulà-parties-jouées";
  try {
    const jouees = JSON.parse(localStorage.getItem(CLEF_PARTIES_JOUÉES) || "[]");
    if (!jouees.includes(iso)) {
      jouees.push(iso);
      localStorage.setItem(CLEF_PARTIES_JOUÉES, JSON.stringify(jouees));
    }
  } catch (erreur) {}
}

function echapperHTML(texte) {
  return texte.replace(/[&<>"']/g, caractere => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[caractere]);
}

function afficherRecap() {
  document.querySelector("#recap").innerHTML = partieActuelle.articles.map((article, index) => {
    const numero = String(index + 1).padStart(2, "0");
    return `
      <li class="recap-item">
        <span class="recap-num">${numero}</span>
        <div class="recap-content">
          <p class="recap-title">${echapperHTML(article.titreOriginal)}</p>
        </div>
        <a class="recap-link" href="${article.lien}" target="_blank" rel="noreferrer">Lire l'article<span aria-hidden="true"> ↗</span></a>
      </li>`;
  }).join("");
}

function messageSelonScore(score) {
  const paliers = [
    { seuil: 24_000, titre: "🧭 GPS humain", message: "Vous n'avez pas besoin de carte. Ce sont les cartes qui ont besoin de vous." },
    { seuil: 22_000, titre: "🏆 Géographe hors pair", message: "Vous connaissez la France par cœur. Votre GPS a pris sa retraite." },
    { seuil: 18_000, titre: "⭐ Très bon sens de l'orientation", message: "Quelques kilomètres de moins et vous décrochiez le titre." },
    { seuil: 13_000, titre: "🗺️ Belle exploration", message: "Vous avez visé la bonne région. La bonne ville attend la prochaine partie." },
    { seuil: 8_000, titre: "🧭 Décollage imminent", message: "Disons que votre boussole est restée à la maison." },
    { seuil: 0, titre: "🧳 Le voyage commence", message: "La France est vaste, et vous avez décidé de la visiter en diagonale." }
  ];
  return paliers.find(palier => score >= palier.seuil);
}

function ouvrirPartage() {
  document.querySelector("#share-overlay").style.display = "flex";
}

function fermerPartage() {
  document.querySelector("#share-overlay").style.display = "none";
}

function messagePartage() {
  return `J'ai marqué ${score.toLocaleString("fr-FR")} points à « ICI ou là » !`;
}

function preparerActionsPartage() {
  document.querySelector("#share-cancel").addEventListener("click", fermerPartage);
  document.querySelector("#share-overlay").addEventListener("click", evenement => {
    if (evenement.target === evenement.currentTarget) fermerPartage();
  });
  document.addEventListener("keydown", evenement => {
    if (evenement.key === "Escape") fermerPartage();
  });

  const url = window.location.href;
  const actions = {
    copy() { copierLien(url); },
    email() { window.location.href = `mailto:?subject=${encodeURIComponent("ICI ou là — mon score !")}&body=${encodeURIComponent(`${messagePartage()}\n\n${url}`)}`; },
    facebook() { window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, "_blank", "noopener"); },
    whatsapp() { window.open(`https://wa.me/?text=${encodeURIComponent(`${messagePartage()} ${url}`)}`, "_blank", "noopener"); },
    bluesky() { window.open(`https://bsky.app/intent/compose?text=${encodeURIComponent(`${messagePartage()} ${url}`)}`, "_blank", "noopener"); }
  };

  document.querySelectorAll("[data-partage]").forEach(option => {
    option.addEventListener("click", evenement => {
      evenement.preventDefault();
      actions[option.dataset.partage]();
      fermerPartage();
    });
  });
}

let minuteurToast;

function afficherToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("toast--visible");
  clearTimeout(minuteurToast);
  minuteurToast = setTimeout(() => toast.classList.remove("toast--visible"), 2000);
}

async function copierLien(url) {
  const confirmation = () => afficherToast("Lien copié !");
  try {
    await navigator.clipboard.writeText(url);
    confirmation();
  } catch (erreur) {
    const zone = document.createElement("textarea");
    zone.value = url;
    zone.setAttribute("readonly", "");
    zone.style.position = "fixed";
    zone.style.opacity = "0";
    document.body.appendChild(zone);
    zone.select();
    try {
      document.execCommand("copy");
      confirmation();
    } catch (erreur2) {
      afficherToast("Copie impossible");
    }
    document.body.removeChild(zone);
  }
}

preparerActionsPartage();
