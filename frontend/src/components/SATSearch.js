import React, { useState, useEffect, useRef } from "react";
import { Input } from "../components/ui/input";
import { Search, X, Loader2 } from "lucide-react";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SATProductSearch = ({ value, onChange, placeholder = "Buscar clave SAT..." }) => {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const wrapperRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    // Handle click outside
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    // If value is set externally, find and display it
    if (value && !selectedItem) {
      setSearch(value);
    }
  }, [value]);

  const searchProducts = async (query) => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(
        `${API_URL}/api/sat/productos/search?q=${encodeURIComponent(query)}&limit=15`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResults(response.data);
    } catch (error) {
      console.error("Error searching SAT products:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    setShowDropdown(true);
    
    // Debounce search
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      searchProducts(val);
    }, 300);
  };

  const handleSelect = (item) => {
    setSelectedItem(item);
    setSearch(item.clave);
    onChange(item.clave);
    setShowDropdown(false);
  };

  const handleClear = () => {
    setSearch("");
    setSelectedItem(null);
    onChange("");
    setResults([]);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-slate-400" />
        <Input
          value={search}
          onChange={handleInputChange}
          onFocus={() => search.length >= 2 && setShowDropdown(true)}
          placeholder={placeholder}
          className="pl-7 pr-7 text-xs h-8"
        />
        {search && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
      
      {showDropdown && (search.length >= 2 || results.length > 0) && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-md shadow-lg max-h-60 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              <span className="ml-2 text-xs text-slate-500">Buscando...</span>
            </div>
          ) : results.length > 0 ? (
            <ul className="py-1">
              {results.map((item) => (
                <li
                  key={item.clave}
                  onClick={() => handleSelect(item)}
                  className="px-3 py-2 hover:bg-blue-50 cursor-pointer border-b border-slate-100 last:border-0"
                >
                  <div className="flex items-start gap-2">
                    <span className="font-mono text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                      {item.clave}
                    </span>
                    <span className="text-xs text-slate-600 flex-1">
                      {item.descripcion}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : search.length >= 2 ? (
            <div className="py-4 text-center text-xs text-slate-500">
              No se encontraron resultados
            </div>
          ) : null}
        </div>
      )}
      
      {selectedItem && (
        <p className="text-[10px] text-slate-500 mt-1 truncate">
          {selectedItem.descripcion}
        </p>
      )}
    </div>
  );
};

const SATUnitSearch = ({ value, onChange }) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [search, setSearch] = useState(value || "");
  const wrapperRef = useRef(null);

  const units = [
    { clave: "H87", descripcion: "Pieza" },
    { clave: "E48", descripcion: "Unidad de Servicio" },
    { clave: "ACT", descripcion: "Actividad" },
    { clave: "KGM", descripcion: "Kilogramo" },
    { clave: "LTR", descripcion: "Litro" },
    { clave: "MTR", descripcion: "Metro" },
    { clave: "MTK", descripcion: "Metro cuadrado" },
    { clave: "MTQ", descripcion: "Metro cúbico" },
    { clave: "XBX", descripcion: "Caja" },
    { clave: "XPK", descripcion: "Paquete" },
    { clave: "SET", descripcion: "Conjunto" },
    { clave: "HUR", descripcion: "Hora" },
    { clave: "DAY", descripcion: "Día" },
    { clave: "MON", descripcion: "Mes" },
    { clave: "ANN", descripcion: "Año" },
    { clave: "XUN", descripcion: "Unidad" },
    { clave: "GRM", descripcion: "Gramo" },
    { clave: "TNE", descripcion: "Tonelada" },
    { clave: "MLT", descripcion: "Mililitro" },
    { clave: "XLT", descripcion: "Lote" },
  ];

  useEffect(() => {
    if (value) setSearch(value);
  }, [value]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredUnits = search
    ? units.filter(
        (u) =>
          u.clave.toLowerCase().includes(search.toLowerCase()) ||
          u.descripcion.toLowerCase().includes(search.toLowerCase())
      )
    : units;

  const handleSelect = (unit) => {
    setSearch(unit.clave);
    onChange(unit.clave);
    setShowDropdown(false);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <Input
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          onChange(e.target.value);
        }}
        onFocus={() => setShowDropdown(true)}
        placeholder="Ej: H87"
        className="text-xs h-8"
      />
      
      {showDropdown && (
        <div className="absolute z-50 w-48 mt-1 bg-white border border-slate-200 rounded-md shadow-lg max-h-48 overflow-auto">
          <ul className="py-1">
            {filteredUnits.map((unit) => (
              <li
                key={unit.clave}
                onClick={() => handleSelect(unit)}
                className="px-3 py-1.5 hover:bg-blue-50 cursor-pointer flex justify-between items-center"
              >
                <span className="font-mono text-xs text-blue-700">{unit.clave}</span>
                <span className="text-[10px] text-slate-500">{unit.descripcion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export { SATProductSearch, SATUnitSearch };
