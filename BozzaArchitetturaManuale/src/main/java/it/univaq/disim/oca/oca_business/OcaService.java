package it.univaq.disim.oca.oca_business;

import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;

import it.univaq.disim.oca.oca_data.OcaData;
import it.univaq.disim.oca.oca_data.OcaDataImpl;
import it.univaq.disim.oca.oca_model.Casella;
import it.univaq.disim.oca.oca_model.Giocatore;
import it.univaq.disim.oca.oca_model.OcaException;
import it.univaq.disim.oca.oca_model.Partita;
import it.univaq.disim.oca.oca_model.TipoCasella;

public class OcaService {

    private static final int BOARD_SIZE = 63;
    private final OcaData ocaData;

    public OcaService() {
        ocaData = new OcaDataImpl();
    }

    public Partita creaPartita(final String nomeGiocatore) throws OcaException {
        validatePlayerName(nomeGiocatore);

        Giocatore giocatore = new Giocatore(nomeGiocatore);
        List<Casella> tabellone = creaTabellone();
        Partita partita = new Partita(giocatore, tabellone);
        ocaData.salvaPartita(partita);
        return partita;
    }

    private void validatePlayerName(final String nomeGiocatore) throws OcaException {
        if (nomeGiocatore == null || nomeGiocatore.trim().isEmpty()) {
            throw new OcaException("Il nome del giocatore non può essere vuoto");
        }
    }

    public Partita getPartita(final Long id) throws OcaException {
        return ocaData.getPartita(id);
    }

    public Partita lanciaDadi(final Long id) throws OcaException {
        Partita partita = ocaData.getPartita(id);
        if (partita == null) {
            throw new OcaException("Partita non trovata");
        }

        SecureRandom secureRandom = new SecureRandom();
        int dado1 = secureRandom.nextInt(6) + 1;
        int dado2 = secureRandom.nextInt(6) + 1;
        int somma = dado1 + dado2;

        Giocatore giocatore = partita.getGiocatore();
        int posizioneCorrente = giocatore.getPosizione();
        int nuovaPosizione = posizioneCorrente + somma;

        List<Casella> tabellone = partita.getTabellone();
        nuovaPosizione = Math.min(nuovaPosizione, tabellone.size() - 1);

        Casella casella = tabellone.get(nuovaPosizione);
        giocatore.setPosizione(nuovaPosizione);

        handleSpecialCasella(casella, giocatore);

        ocaData.aggiornaPartita(partita);
        return partita;
    }

    private void handleSpecialCasella(final Casella casella, final Giocatore giocatore) {
        if (casella.getTipo() == TipoCasella.OCA || casella.getTipo() == TipoCasella.PONTE) {
            giocatore.setPosizione(casella.getNumero());
        }
    }

    private List<Casella> creaTabellone() {
        List<Casella> tabellone = new ArrayList<>(BOARD_SIZE);
        for (int i = 0; i < BOARD_SIZE; i++) {
            tabellone.add(createCasella(i));
        }
        return tabellone;
    }

    private Casella createCasella(final int i) {
        if (isPonteCasella(i)) {
            return new Casella(i, TipoCasella.PONTE);
        } else if (isOcaCasella(i)) {
            return new Casella(i, TipoCasella.OCA);
        } else {
            return new Casella(i, TipoCasella.NORMALE);
        }
    }

    private boolean isPonteCasella(final int i) {
        return i % 6 == 0 && i != 0 && i < 54;
    }

    private boolean isOcaCasella(final int i) {
        return (i % 5 == 0 || i % 9 == 0 || i % 14 == 0 || i % 17 == 0 || i % 22 == 0 || i % 26 == 0 || i % 31 == 0 ||
                i % 35 == 0 || i % 40 == 0 || i % 44 == 0 || i % 49 == 0 || i % 53 == 0 || i % 58 == 0) && i != 0;
    }
}