// See www.openfst.org for extensive documentation on this weighted
// finite-state transducer library.
//
// Sparse version of tuple-weight, based on tuple-weight.h.
// Internally stores sparse key, value pairs in linked list. The default value
// element is the assumed value of unset keys. Internal singleton
// implementation that stores first key, value pair as a initialized member
// variable to avoid unnecessary allocation on heap. Use
// SparseTupleWeightIterator to iterate through the key,value pairs. Note:
// this does NOT iterate through the default value.
//
// Sparse tuple weight set operation definitions.

#ifndef FST_LIB_SPARSE_TUPLE_WEIGHT_H_
#define FST_LIB_SPARSE_TUPLE_WEIGHT_H_

#include <list>
#include <stack>
#include <string>
#include <unordered_map>
#include <utility>


#include <fst/weight.h>


namespace fst {

template <class W, class K>
class SparseTupleWeightIterator;

// Arbitrary dimension tuple weight, stored as a sorted linked-list.
// W is any weight class, and K is the key value type. kNoKey (-1) is reserved
// for internal use.
template <class W, class K = int>
class SparseTupleWeight {
 public:
  using ReverseWeight = SparseTupleWeight<typename W::ReverseWeight, K>;

  using Pair = std::pair<K, W>;

  constexpr static K kNoKey = -1;

  SparseTupleWeight() { Init(); }

  template <class Iterator>
  SparseTupleWeight(Iterator begin, Iterator end) {
    Init();
    // Assumes input iterator is sorted.
    for (auto it = begin; it != end; ++it) Push(*it);
  }

  SparseTupleWeight(const K &key, const W &weight) {
    Init();
    Push(key, weight);
  }

  explicit SparseTupleWeight(const W &weight) { Init(weight); }

  SparseTupleWeight(const SparseTupleWeight &weight) {
    Init(weight.DefaultValue());
    SetDefaultValue(weight.DefaultValue());
    for (SparseTupleWeightIterator<W, K> it(weight); !it.Done(); it.Next()) {
      Push(it.Value());
    }
  }

  static const SparseTupleWeight &Zero() {
    static const SparseTupleWeight zero(W::Zero());
    return zero;
  }

  static const SparseTupleWeight &One() {
    static const SparseTupleWeight one(W::One());
    return one;
  }

  static const SparseTupleWeight &NoWeight() {
    static const SparseTupleWeight no_weight(W::NoWeight());
    return no_weight;
  }

  std::istream &Read(std::istream &strm) {
    ReadType(strm, &default_);
    ReadType(strm, &first_);
    return ReadType(strm, &rest_);
  }

  std::ostream &Write(std::ostream &strm) const {
    WriteType(strm, default_);
    WriteType(strm, first_);
    return WriteType(strm, rest_);
  }

  SparseTupleWeight &operator=(const SparseTupleWeight &weight) {
    if (this == &weight) return *this;  // Checks for identity.
    Init(weight.DefaultValue());
    for (SparseTupleWeightIterator<W, K> it(weight); !it.Done(); it.Next()) {
      Push(it.Value());
    }
    return *this;
  }

  bool Member() const {
    if (!DefaultValue().Member()) return false;
    for (SparseTupleWeightIterator<W, K> it(*this); !it.Done(); it.Next()) {
      if (!it.Value().second.Member()) return false;
    }
    return true;
  }

  // Assumes H() function exists for the hash of the key value.
  size_t Hash() const {
    size_t h = 0;
    static const std::hash<K> H;
    for (SparseTupleWeightIterator<W, K> it(*this); !it.Done(); it.Next()) {
      h = 5 * h + H(it.Value().first);
      h = 13 * h + it.Value().second.Hash();
    }
    return h;
  }

  SparseTupleWeight Quantize(float delta = kDelta) const {
    SparseTupleWeight weight;
    for (SparseTupleWeightIterator<W, K> it(*this); !it.Done(); it.Next()) {
      weight.Push(it.Value().first, it.Value().second.Quantize(delta));
    }
    return weight;
  }

  ReverseWeight Reverse() const {
    SparseTupleWeight weight;
    for (SparseTupleWeightIterator<W, K> it(*this); !it.Done(); it.Next()) {
      weight.Push(it.Value().first, it.Value().second.Reverse());
    }
    return ReverseWeight(weight);
  }

  void Init(const W &default_value = W::Zero()) {
    first_.first = kNoKey;
    // Initialized to the reserved key value.
    default_ = default_value;
    rest_.clear();
  }

  size_t Size() const {
    if (first_.first == kNoKey) {
      return 0;
    } else {
      return rest_.size() + 1;
    }
  }

  inline void Push(const K &key, const W &weight,
                   bool default_value_check = true) {
    Push(std::make_pair(key, weight), default_value_check);
  }

  inline void Push(const Pair &pair, bool default_value_check = true) {
    if (default_value_check && pair.second == default_) return;
    if (first_.first == kNoKey) {
      first_ = pair;
    } else {
      rest_.push_back(pair);
    }
  }

  void SetDefaultValue(const W &value) { default_ = value; }

  const W &DefaultValue() const { return default_; }

 private:
  // Assumed default value of uninitialized keys, by default W::Zero().
  W default_;

  // Key values pairs are first stored in first_, then fill rest_ this way we
  // can avoid dynamic allocation in the common case where the weight is a
  // single key/value pair.
  Pair first_;
  std::list<Pair> rest_;

  friend class SparseTupleWeightIterator<W, K>;
};

template <class W, class K>
class SparseTupleWeightIterator {
 public:
  using Pair = typename SparseTupleWeight<W, K>::Pair;
  using const_iterator = typename std::list<Pair>::const_iterator;
  using iterator = typename std::list<Pair>::iterator;

  explicit SparseTupleWeightIterator(const SparseTupleWeight<W, K> &weight)
      : first_(weight.first_),
        rest_(weight.rest_),
        init_(true),
        iter_(rest_.begin()) {}

  bool Done() const {
    if (init_) {
      return first_.first == SparseTupleWeight<W, K>::kNoKey;
    } else {
      return iter_ == rest_.end();
    }
  }

  const Pair &Value() const { return init_ ? first_ : *iter_; }

  void Next() {
    if (init_) {
      init_ = false;
    } else {
      ++iter_;
    }
  }

  void Reset() {
    init_ = true;
    iter_ = rest_.begin();
  }

 private:
  const Pair &first_;
  const std::list<Pair> &rest_;
  bool init_;  // In the initialized state?
  const_iterator iter_;
};

template <class W, class K, class M>
inline void SparseTupleWeightMap(SparseTupleWeight<W, K> *result,
                                 const SparseTupleWeight<W, K> &w1,
                                 const SparseTupleWeight<W, K> &w2,
                                 const M &operator_mapper) {
  SparseTupleWeightIterator<W, K> w1_it(w1);
  SparseTupleWeightIterator<W, K> w2_it(w2);
  const auto &v1_def = w1.DefaultValue();
  const auto &v2_def = w2.DefaultValue();
  result->SetDefaultValue(operator_mapper.Map(0, v1_def, v2_def));
  while (!w1_it.Done() || !w2_it.Done()) {
    const auto &k1 = (w1_it.Done()) ? w2_it.Value().first : w1_it.Value().first;
    const auto &k2 = (w2_it.Done()) ? w1_it.Value().first : w2_it.Value().first;
    const auto &v1 = (w1_it.Done()) ? v1_def : w1_it.Value().second;
    const auto &v2 = (w2_it.Done()) ? v2_def : w2_it.Value().second;
    if (k1 == k2) {
      result->Push(k1, operator_mapper.Map(k1, v1, v2));
      if (!w1_it.Done()) w1_it.Next();
      if (!w2_it.Done()) w2_it.Next();
    } else if (k1 < k2) {
      result->Push(k1, operator_mapper.Map(k1, v1, v2_def));
      w1_it.Next();
    } else {
      result->Push(k2, operator_mapper.Map(k2, v1_def, v2));
      w2_it.Next();
    }
  }
}

template <class W, class K>
inline bool operator==(const SparseTupleWeight<W, K> &w1,
                       const SparseTupleWeight<W, K> &w2) {
  const auto &v1_def = w1.DefaultValue();
  const auto &v2_def = w2.DefaultValue();
  if (v1_def != v2_def) return false;
  SparseTupleWeightIterator<W, K> w1_it(w1);
  SparseTupleWeightIterator<W, K> w2_it(w2);
  while (!w1_it.Done() || !w2_it.Done()) {
    const auto &k1 = (w1_it.Done()) ? w2_it.Value().first : w1_it.Value().first;
    const auto &k2 = (w2_it.Done()) ? w1_it.Value().first : w2_it.Value().first;
    const auto &v1 = (w1_it.Done()) ? v1_def : w1_it.Value().second;
    const auto &v2 = (w2_it.Done()) ? v2_def : w2_it.Value().second;
    if (k1 == k2) {
      if (v1 != v2) return false;
      if (!w1_it.Done()) w1_it.Next();
      if (!w2_it.Done()) w2_it.Next();
    } else if (k1 < k2) {
      if (v1 != v2_def) return false;
      w1_it.Next();
    } else {
      if (v1_def != v2) return false;
      w2_it.Next();
    }
  }
  return true;
}

template <class W, class K>
inline bool operator!=(const SparseTupleWeight<W, K> &w1,
                       const SparseTupleWeight<W, K> &w2) {
  return !(w1 == w2);
}

template <class W, class K>
inline std::ostream &operator<<(std::ostream &strm,
                                const SparseTupleWeight<W, K> &weight) {
  CompositeWeightWriter writer(strm);
  writer.WriteBegin();
  writer.WriteElement(weight.DefaultValue());
  for (SparseTupleWeightIterator<W, K> it(weight); !it.Done(); it.Next()) {
    writer.WriteElement(it.Value().first);
    writer.WriteElement(it.Value().second);
  }
  writer.WriteEnd();
  return strm;
}

template <class W, class K>
inline std::istream &operator>>(std::istream &strm,
                                SparseTupleWeight<W, K> &weight) {
  CompositeWeightReader reader(strm);
  reader.ReadBegin();
  W def;
  bool more = reader.ReadElement(&def);
  weight.Init(def);
  while (more) {
    K key;
    reader.ReadElement(&key);
    W v;
    more = reader.ReadElement(&v);
    weight.Push(key, v);
  }
  reader.ReadEnd();
  return strm;
}

}  // namespace fst

#endif  // FST_LIB_SPARSE_TUPLE_WEIGHT_H_
