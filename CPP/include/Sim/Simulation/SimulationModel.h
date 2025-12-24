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
#include "../../Core/Base.h"
#include "../SimTypeDefs.h"
#include <string>

// THIS CLASS WILL BE VISIBLE TO AN API CLIENT.
// THIS HEADER FILE WILL BE GENERATED FROM NIDL.
#include "../../Core/OSMacros.h"

#ifdef SIMXINTERFACE_EXPORTS
# ifdef __COMPILING_ADSK_SIM_SIMULATIONMODEL_CPP__
# define ADSK_SIM_SIMULATIONMODEL_API XI_EXPORT
# else
# define ADSK_SIM_SIMULATIONMODEL_API
# endif
#else
# define ADSK_SIM_SIMULATIONMODEL_API XI_IMPORT
#endif

namespace adsk { namespace fusion {
    class WorkingModel;
}}
namespace adsk { namespace sim {
    class Simulations;
    class Studies;
}}

namespace adsk { namespace sim {

/// !!!!! Warning !!!!!
/// ! This is hidden and not officially supported
/// !!!!! Warning !!!!!
/// 
/// Object that represents a simulation model inside the simulation environment.
class SimulationModel : public core::Base {
public:

    /// The name of the simulation model as displayed in the browser.
    std::string name() const;
    bool name(const std::string& value);

    /// The parent Simulations object.
    core::Ptr<Simulations> parentSimulations() const;

    /// The Studies collection that provides access to existing studies in the simulation model.
    core::Ptr<Studies> studies() const;

    /// The ModelComponents that provides access to Bodies/Components in the model.
    core::Ptr<fusion::WorkingModel> modelComponents() const;

    ADSK_SIM_SIMULATIONMODEL_API static const char* classType();
    ADSK_SIM_SIMULATIONMODEL_API const char* objectType() const override;
    ADSK_SIM_SIMULATIONMODEL_API void* queryInterface(const char* id) const override;
    ADSK_SIM_SIMULATIONMODEL_API static const char* interfaceId() { return classType(); }

private:

    // Raw interface
    virtual char* name_raw() const = 0;
    virtual bool name_raw(const char* value) = 0;
    virtual Simulations* parentSimulations_raw() const = 0;
    virtual Studies* studies_raw() const = 0;
    virtual fusion::WorkingModel* modelComponents_raw() const = 0;
};

// Inline wrappers

inline std::string SimulationModel::name() const
{
    std::string res;

    char* p= name_raw();
    if (p)
    {
        res = p;
        core::DeallocateArray(p);
    }
    return res;
}

inline bool SimulationModel::name(const std::string& value)
{
    return name_raw(value.c_str());
}

inline core::Ptr<Simulations> SimulationModel::parentSimulations() const
{
    core::Ptr<Simulations> res = parentSimulations_raw();
    return res;
}

inline core::Ptr<Studies> SimulationModel::studies() const
{
    core::Ptr<Studies> res = studies_raw();
    return res;
}

inline core::Ptr<fusion::WorkingModel> SimulationModel::modelComponents() const
{
    core::Ptr<fusion::WorkingModel> res = modelComponents_raw();
    return res;
}
}// namespace sim
}// namespace adsk

#undef ADSK_SIM_SIMULATIONMODEL_API