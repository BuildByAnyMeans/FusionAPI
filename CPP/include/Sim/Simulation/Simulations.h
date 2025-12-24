//////////////////////////////////////////////////////////////////////////////
//
// Copyright 2025 Autodesk, Inc. All rights reserved.
//
// Use of this software is subject to the terms of the Autodesk license
// agreement provided at the time of installation or download, or which
// otherwise accompanies this software.
//
//////////////////////////////////////////////////////////////////////////////

#pragma once
#include "../../Core/Application/Product.h"

// THIS CLASS WILL BE VISIBLE TO AN API CLIENT.
// THIS HEADER FILE WILL BE GENERATED FROM NIDL.
#include "../../Core/OSMacros.h"

#ifdef SIMXINTERFACE_EXPORTS
# ifdef __COMPILING_ADSK_SIM_SIMULATIONS_CPP__
# define ADSK_SIM_SIMULATIONS_API XI_EXPORT
# else
# define ADSK_SIM_SIMULATIONS_API
# endif
#else
# define ADSK_SIM_SIMULATIONS_API XI_IMPORT
#endif

namespace adsk { namespace sim {
    class SimulationModel;
}}

namespace adsk { namespace sim {

/// !!!!! Warning !!!!!
/// ! This is hidden and not officially supported
/// !!!!! Warning !!!!!
/// 
/// Object that represents the simulations environment of a Fusion document.
class Simulations : public core::Product {
public:

    /// Function that returns the specified simulation model using an index into the collection.
    /// index : The index of the item within the collection to return. The first item in the collection has an index of 0.
    /// Returns the specified item or null if an invalid index was specified.
    core::Ptr<SimulationModel> item(size_t index) const;

    /// The number of simulation models.
    size_t count() const;

    typedef SimulationModel iterable_type;
    template <class OutputIterator> void copyTo(OutputIterator result);

    ADSK_SIM_SIMULATIONS_API static const char* classType();
    ADSK_SIM_SIMULATIONS_API const char* objectType() const override;
    ADSK_SIM_SIMULATIONS_API void* queryInterface(const char* id) const override;
    ADSK_SIM_SIMULATIONS_API static const char* interfaceId() { return classType(); }

private:

    // Raw interface
    virtual SimulationModel* item_raw(size_t index) const = 0;
    virtual size_t count_raw() const = 0;
};

// Inline wrappers

inline core::Ptr<SimulationModel> Simulations::item(size_t index) const
{
    core::Ptr<SimulationModel> res = item_raw(index);
    return res;
}

inline size_t Simulations::count() const
{
    size_t res = count_raw();
    return res;
}

template <class OutputIterator> inline void Simulations::copyTo(OutputIterator result)
{
    for (size_t i = 0;i < count();++i)
    {
        *result = item(i);
        ++result;
    }
}
}// namespace sim
}// namespace adsk

#undef ADSK_SIM_SIMULATIONS_API