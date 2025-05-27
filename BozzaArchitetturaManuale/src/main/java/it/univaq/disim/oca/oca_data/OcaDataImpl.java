package it.univaq.disim.oca.oca_data;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

import it.univaq.disim.oca.oca_model.OcaException;
import it.univaq.disim.oca.oca_model.Partita;

public class OcaDataImpl implements OcaData {

    private final Map<Long, Partita> partite;
    private Long idCounter;

    public OcaDataImpl() {
        partite = new HashMap<>();
        idCounter = 0L;
    }

    @Override
    public void salvaPartita(final Partita partita) throws OcaException {
        Objects.requireNonNull(partita, "La partita non può essere nulla");

        idCounter++;
        partita.setId(idCounter);
        partite.put(idCounter, partita);
    }

    @Override
    public Partita getPartita(final Long id) throws OcaException {
        Objects.requireNonNull(id, "L'id non può essere nullo");

        Partita partita = partite.get(id);
        if (partita == null) {
            throw new OcaException("Partita non trovata");
        }

        return partita;
    }

    @Override
    public void aggiornaPartita(final Partita partita) throws OcaException {
        Objects.requireNonNull(partita, "La partita non può essere nulla");
        Objects.requireNonNull(partita.getId(), "L'id della partita non può essere nullo");

        partite.put(partita.getId(), partita);
    }
}